from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pinecone_service import pinecone_service
from paralegals.tax import tax_paralegal
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
        print("results=====================================================================================", results)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.post("/ask")
async def ask_endpoint(query: str)->str:
    #TODO: write a proper response model
    try:
        response = tax_paralegal.ask_tax_paralegal(query)
        print(response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))