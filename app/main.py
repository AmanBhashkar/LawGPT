from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pinecone
from pinecone_service import pinecone_service
import os

app = FastAPI()


class ChatMessage(BaseModel):
    content: str
    user_id: str

class VectorQuery(BaseModel):
    query: str
    top_k: int = 12

@app.post("/chat")
async def chat_endpoint(message: ChatMessage):
    # TODO: Add ChatGPT interaction and vector storage logic
    return {"response": "TODO", "vector": []}

@app.post("/search")
async def vector_search(query: VectorQuery):
    try:
        print(query.query)
        results = pinecone_service.semantic_search(query.query, query.top_k)
        print(results)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 