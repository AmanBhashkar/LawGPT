from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi import websockets
from pydantic import BaseModel
from pinecone_service import pinecone_service
from paralegals.tax import legal_paralegal
from ai_service.agent_schema import AgentResponse
import os
from typing import Dict
import uuid
import json
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active websocket connections
active_connections: Dict[str, WebSocket] = {}

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
async def ask_endpoint(query: str) -> AgentResponse:
    """Endpoint for any legal questions (handles all domains)"""
    try:
        response = await legal_paralegal.ask_legal_paralegal(query)
        return response.message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.websocket("/ws/legal/{client_id}")
async def legal_websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for legal questions with real-time responses"""
    await websocket.accept()
    active_connections[client_id] = websocket
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "client_id": client_id,
            "message": "Connected to legal paralegal service"
        })
        
        while True:
            data = await websocket.receive_text()
            try:
                request_data = json.loads(data)
                query = request_data.get("query", "")
                print(f"Received query from client {client_id}: {query}")
                
                if not query:
                    await websocket.send_json({
                        "type": "error",
                        "message": "No query provided"
                    })
                    continue
                
                # Send acknowledgment that processing has started
                await websocket.send_json({
                    "type": "processing",
                    "message": "Processing your legal question..."
                })
                
                # Initialize context variables with client_id for session tracking
                context_variables = {"chat_id": client_id}
                
                # Process the query
                response = await legal_paralegal.ask_legal_paralegal(query)
                
                # Handle either string or AgentResponse
                response_content = response
                if hasattr(response, "message"):
                    response_content = response.message
                
                # Send the final response
                await websocket.send_json({
                    "type": "result",
                    "response": response_content
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            except Exception as e:
                print(f"Error processing request: {str(e)}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Error processing request: {str(e)}"
                })
                
    except WebSocketDisconnect:
        if client_id in active_connections:
            del active_connections[client_id]
        print(f"Client {client_id} disconnected")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        if client_id in active_connections:
            await websocket.send_json({
                "type": "error",
                "message": f"Server error: {str(e)}"
            })
            del active_connections[client_id]

# Commented out POST endpoints as they are replaced by WebSocket
# @app.post("/ask")
# async def ask_endpoint(query: str) -> AgentResponse:
#     """Endpoint for tax-related questions (legacy support)"""
#     try:
#         response = await tax_paralegal.ask_tax_paralegal(query)
#         print(response)
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @app.post("/ask/legal")
# async def ask_legal_endpoint(query: str) -> AgentResponse:
#     """Endpoint for any legal questions (handles all domains)"""
#     try:
#         response = await legal_paralegal.ask_legal_paralegal(query)
#         print(response)
#         return response
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))