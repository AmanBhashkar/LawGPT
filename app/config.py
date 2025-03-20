import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
    OPENAI_EMBEDDINGS_MODEL: str = os.getenv("OPENAI_EMBEDDINGS_MODEL", "text-embedding-ada-002")
    OPENAI_EMBEDDINGS_DIMENSION: int = int(os.getenv("OPENAI_EMBEDDINGS_DIMENSION", "1536"))
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX")
    PINECONE_NAMESPACE: str = os.getenv("PINECONE_NAMESPACE")
    GEMENI_API_KEY: str = os.getenv("GEMENI_API_KEY")
    TAX_PARALEGAL_MODEL: str = os.getenv("TAX_PARALEGAL_MODEL")
    TAX_PARALEGAL_VECTOR_STORE: str = os.getenv("TAX_PARALEGAL_VECTOR_STORE")
settings = Settings()