import streamlit as st
import asyncio
import websockets
import json

# WebSocket URL
WEBSOCKET_URL = "ws://localhost:8000/ws/legal/"
import streamlit as st
import asyncio
import websockets
import json

async def websocket_connect(client_id, query, message_container):
    """Connects to the WebSocket server and sends/receives messages."""
    uri = f"ws://localhost:8000/ws/legal/{client_id}"  # Replace with your WebSocket URI
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({"query": query}))

        async for message in websocket:
            try:
                data = json.loads(message)
                message_type = data.get("type")

                if message_type == "connection_established":
                    message_container.write(f"Connected: {data.get('message')}")
                elif message_type == "processing":
                    message_container.write(f"Processing: {data.get('message')}")
                elif message_type == "result":
                    message_container.write(f"Response: {data.get('response')}")
                elif message_type == "error":
                    message_container.error(f"Error: {data.get('message')}")
                else:
                    message_container.write(f"Unknown message: {message}")

            except json.JSONDecodeError:
                message_container.write(f"Received non-JSON message: {message}")
            except Exception as e:
                message_container.error(f"Error handling message: {e}")

def main():
    st.title("Legal Chat UI")

    client_id = st.text_input("Client ID", "default_client")
    query = st.text_area("Enter your legal question", height=150)

    message_container = st.empty() # Create an empty container to hold the messages

    if st.button("Send"):
        if query:
            asyncio.run(websocket_connect(client_id, query, message_container))
        else:
            st.warning("Please enter a query.")

if __name__ == "__main__":
    main()