from typing import Optional
# from litellm import completion
from config import settings
from pinecone import Pinecone, ServerlessSpec  # Import Pinecone class
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core import Settings as LlamaIndexSettings
from llama_index.llms.gemini import Gemini

# Use OpenAI embeddings for 1536 dimensions to match your Pinecone index
embed_model = OpenAIEmbedding(
    model=settings.OPENAI_EMBEDDINGS_MODEL,
    api_key=settings.OPENAI_API_KEY
)
LlamaIndexSettings.embed_model = embed_model

# Set Gemini as the default LLM
llm_model = Gemini(api_key=settings.GEMENI_API_KEY, model_name="models/gemini-2.0-flash")
LlamaIndexSettings.llm = llm_model

# Create an instance of Pinecone with your API key
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Check if the index exists, create it if it doesn't
if settings.PINECONE_INDEX not in pc.list_indexes().names():
    pc.create_index(
        name=settings.PINECONE_INDEX,
        dimension=1536,  # Use 1536 dimensions to match OpenAI embeddings
        metric='euclidean',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-west-2'
        )
    )

class AIBase:
    def __init__(self, model: str = "gemini-pro", vector_store: Optional[PineconeVectorStore] = None):
        if vector_store is None:
            # Create an instance of pinecone.Index
            index = pc.Index(settings.PINECONE_INDEX)  # Use the Pinecone instance to get the index
            vector_store = PineconeVectorStore(
                index=index,
                index_name=settings.PINECONE_INDEX  # Add the index_name parameter
            )
        self.model = model
        self.vector_store = vector_store

    # def ask(self, query: str) -> str:
    #     #TODO:
    #     return completion(model=self.model, prompt=query)
    
ai_base = AIBase()