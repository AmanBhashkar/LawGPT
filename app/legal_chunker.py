import re
import spacy
from typing import List, Dict, Any

class LegalDocumentChunker:
    def __init__(self, window_size=3, overlap=1, max_chunk_size=500):
        """
        Initialize the chunker with spaCy model and configuration
        window_size: Number of sentences to include in each chunk
        overlap: Number of sentences to overlap between chunks
        max_chunk_size: Maximum number of tokens in a chunk
        """
        self.nlp = spacy.load("en_core_web_lg")
        self.nlp.max_length = 100000  # Set a reasonable chunk size for spaCy
        self.window_size = window_size
        self.overlap = overlap
        self.max_chunk_size = max_chunk_size

    def initial_split(self, content: str, max_length=90000) -> List[str]:
        """Split content into processable chunks based on paragraphs.
        content: The content to be chunked
        max_length: Maximum number of tokens in a chunk
        """
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            if current_length + para_length > max_length:
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                current_chunk = [para]
                current_length = para_length
            else:
                current_chunk.append(para)
                current_length += para_length
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        return chunks

    def process_chunk(self, text: str) -> List[str]:
        """Process a single chunk that's within spaCy's length limits"""
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        chunks = []
        
        # Implement sliding window with overlap
        start = 0
        while start < len(sentences):
            end = start + self.window_size
            window = sentences[start:end]
            
            # Calculate actual token count using spaCy's tokenization
            token_count = sum(len(sent) for sent in doc[start:end])
            
            # Handle oversized windows immediately
            while token_count > self.max_chunk_size and len(window) > 1:
                # Reduce window size incrementally
                window = window[:-1]
                end -= 1
                token_count = sum(len(sent) for sent in doc[start:end])
            
            chunk_text = ' '.join(window)
            
            # Final safety check
            if token_count > self.max_chunk_size:
                # Split at sentence boundary if still too large
                chunk_text = self._split_oversized_sentence(window[0])
                
            chunks.append(chunk_text)
            
            # Move window by step size (window_size - overlap)
            start += (self.window_size - self.overlap)
        
        return chunks

    def _split_oversized_sentence(self, sentence: str) -> List[str]:
        """Split a single sentence that exceeds max chunk size"""
        chunks = []
        words = sentence.split()
        for i in range(0, len(words), self.max_chunk_size):
            chunks.append(' '.join(words[i:i+self.max_chunk_size]))
        return chunks

    def _find_optimal_split(self, window: List[str]) -> int:
        """Find mid-point between paragraphs if possible"""
        mid = len(window) // 2
        for i in range(mid, 0, -1):
            if '\n\n' in window[i]:
                return i + 1
        return mid

    def chunk_document(self, content: str) -> List[str]:
        # First, split into manageable chunks
        initial_chunks = self.initial_split(content)
        
        # Process each chunk
        final_chunks = []
        for chunk in initial_chunks:
            processed_chunks = self.process_chunk(chunk)
            final_chunks.extend(processed_chunks)
        
        return self._postprocess_chunks(final_chunks)

    def _postprocess_chunks(self, chunks: List[str]) -> List[str]:
        # Improved merging logic
        merged = []
        current_chunk = []
        current_token_count = 0
        
        for chunk in chunks:
            chunk_tokens = chunk.split()
            chunk_token_count = len(chunk_tokens)
            
            if current_token_count + chunk_token_count <= self.max_chunk_size:
                current_chunk.append(chunk)
                current_token_count += chunk_token_count
            else:
                if current_chunk:
                    merged.append(' '.join(current_chunk))
                current_chunk = [chunk]
                current_token_count = chunk_token_count
        
        if current_chunk:
            final_chunk = ' '.join(current_chunk)
            if len(final_chunk.split()) > self.max_chunk_size:
                merged.extend(self._split_oversized_sentence(final_chunk))
            else:
                merged.append(final_chunk)
                
        return merged

    def save_chunks(self, chunks: List[str], filename: str):
        """Save chunks to file with separation boundaries"""
        with open(filename, 'w') as f:
            f.write('\n==========================\n'.join(chunks))

# Usage
# if __name__ == "__main__":
#     chunker = LegalDocumentChunker()
    
#     # Read the document
#     print("Reading document...")
#     with open('income_tax_act_1961.md', 'r') as f:
#         content = f.read()
    
#     # Process the document
#     print("Processing document...")
#     chunks = chunker.chunk_document(content)
    
#     # Save the chunks
#     print("Saving chunks...")
#     chunker.save_chunks(chunks, 'legal_chunks_v4.txt')
#     print(f"Processing complete. Generated {len(chunks)} chunks.")

legal_chunker = LegalDocumentChunker()