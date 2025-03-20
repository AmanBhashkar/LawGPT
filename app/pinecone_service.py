import os
from typing import Dict, List, Callable
import pandas as pd
from tqdm import tqdm
from config import settings
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore

class SentenceTransformerWrapper:
    """Adapter for SentenceTransformer to match LangChain interface"""
    def __init__(self, model_name: str = 'sentence-transformers/multi-qa-mpnet-base-dot-v1', device: str = 'cpu'):
        self.model = SentenceTransformer(model_name, device=device)
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, convert_to_tensor=False).tolist()
    
    def embed_query(self, text: str) -> List[float]:
        return self.model.encode(text, convert_to_tensor=False).tolist()

class PineconeService:
    def __init__(self):
        """
        Initialize Pinecone service with the required settings
        
        Args:
            settings: Application settings containing Azure and Pinecone configurations
        """
        # Use the 1536-dimensional model for embeddings
        self.embedding_dimension = 1536  # Dimension for model output
        self.embeddings = self._initialize_embeddings()
        self.vector_store = self._initialize_vector_store()

    def _initialize_embeddings(self) -> SentenceTransformerWrapper:
        """Initialize Sentence Transformer model with wrapper"""
        return SentenceTransformerWrapper(
            # Use the 1536-dimensional model
            model_name='sangmini/msmarco-cotmae-MiniLM-L12_en-ko-ja',  # 1536-dimensional model
            device='cpu'
        )

    def _initialize_vector_store(self) -> PineconeVectorStore:
        """Initialize and return Pinecone vector store"""
        return PineconeVectorStore(
            pinecone_api_key=settings.PINECONE_API_KEY,
            index_name=settings.PINECONE_INDEX,
            embedding=self.embeddings
        )

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embeddings using Sentence Transformers.
        """
        try:
            text = self._prepare_text_for_embedding(text)
            embedding = self.embeddings.embed_query(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding for text: {text[:100]}...")
            print(f"Error details: {str(e)}")
            raise

    def _prepare_text_for_embedding(self, text: str) -> str:
        """Prepare text for embedding by cleaning and truncating if necessary"""
        if text is None or not isinstance(text, str):
            text = str(text)

        text = text.replace("\x00", "").strip()

        if not text:
            text = "empty_document"

        # Adjust max tokens based on model requirements
        max_tokens = 512  # Typical limit for transformer models
        if len(text) > max_tokens:
            text = text[:max_tokens]

        return text

    def store_document_data(self, df: pd.DataFrame, document_id: str) -> None:
        """
        Store processed document data in Pinecone.
        
        Args:
            df: DataFrame containing processed document data
            document_id: Unique identifier for the document
        """
        try:
            print("Storing document data in Pinecone...")
            documents = self._prepare_documents_for_storage(df, document_id)

            if not documents:
                raise ValueError("No valid pages to store in Pinecone")

            self.vector_store.add_documents(documents)
            print(f"Successfully stored {len(documents)} pages in Pinecone")

        except Exception as e:
            print(f"Error storing data in Pinecone: {e}")
            raise

    def _prepare_documents_for_storage(self, df: pd.DataFrame, document_id: str) -> List[Document]:
        """Prepare documents for storage in Pinecone"""
        documents = []

        for _idx, row in tqdm(df.iterrows(), total=len(df), desc="Preparing data for Pinecone"):
            try:
                page_text = str(row["PageText"]).strip()
                if not page_text:
                    print(f"Warning: Empty text for page {row['PageNumber']}, skipping...")
                    continue

                metadata = {
                    "document_id": document_id,
                    "page_number": str(row["PageNumber"]),
                    "image_path": str(row["ImagePath"]),
                    "has_visual_content": "Y" if self._has_visual_content(page_text) else "N",
                    "document_type": "pdf",
                    "document_name": "Freddie Mac",
                }

                documents.append(Document(
                    page_content=page_text,
                    metadata=metadata
                ))
            except Exception as e:
                print(f"Error processing page {row['PageNumber']}: {str(e)}")
                continue

        return documents

    def _has_visual_content(self, text: str) -> bool:
        """Check if the text contains visual content markers"""
        return "DESCRIPTION OF THE IMAGE OR CHART" in text or "TRANSCRIPTION OF THE TABLE" in text

    def semantic_search(self, query: str, top_k: int = 12) -> List[Dict]:
        """
        Perform semantic search on stored documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of search results with metadata
        
        Raises:
            VectorStoreError: If search operation fails
        """
        try:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=top_k
            )
            return [self._format_search_result(doc, score) for doc, score in results]
        except Exception as e:
            print(f"Error performing semantic search: {e}")
            raise

    def _format_search_result(self, doc: Document, score: float) -> Dict:
        """
        Format a search result for return
        
        Args:
            doc: Search result from Pinecone
            score: Similarity score
        
        Returns:
            Dictionary containing formatted search result
        """
        metadata = doc.metadata
        return {
            "page_id": f"{metadata.get('document_id')}-page-{metadata.get('page_number')}",
            "user_document_id": metadata.get("document_id", ""),
            "page_number": metadata.get("page_number", ""),
            "image_path": metadata.get("image_path", ""),
            "has_visual_content": metadata.get("has_visual_content", ""),
            "content": doc.page_content,
            "similarity_score": 1 - score if score <= 1 else score,
        }

    def store_legal_chunks(self, chunks: List[str], document_id: str, progress_bar: tqdm) -> None:
        """
        Store legal document chunks in Pinecone with progress tracking
        
        Args:
            chunks: List of text chunks to store
            document_id: Unique identifier for the document
            progress_bar: tqdm progress bar instance
        """
        try:
            documents = []
            for idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    print(f"Warning: Empty chunk at index {idx}, skipping...")
                    continue
                
                metadata = {
                    "document_id": document_id,
                    "chunk_number": str(idx + 1),
                    "document_type": "legal",
                    "source": "LegalDocumentChunker"
                }
                
                documents.append(Document(
                    page_content=chunk,
                    metadata=metadata
                ))
                progress_bar.update(1)  # Update progress bar
            
            if documents:
                self.vector_store.add_documents(documents)
                print(f"Successfully stored {len(documents)} legal chunks in Pinecone")
            else:
                print("No valid chunks to store")
                
        except Exception as e:
            print(f"Error storing legal chunks in Pinecone: {e}")
            raise

pinecone_service = PineconeService()
