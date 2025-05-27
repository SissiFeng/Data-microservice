from litestar import Router, websocket # Changed APIRouter to Router, imported websocket decorator
from litestar.connection import WebSocket # Changed WebSocket import
from litestar.exceptions import WebSocketDisconnect # Changed WebSocketDisconnect import
from typing import Dict, List
import json
import asyncio

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {} # Type hint updated to litestar.connection.WebSocket
    
    async def connect(self, socket: WebSocket, client_id: str): # Renamed websocket to socket, type hint updated
        await socket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(socket)
    
    def disconnect(self, socket: WebSocket, client_id: str): # Renamed websocket to socket, type hint updated
        if client_id in self.active_connections:
            if socket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(socket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
    
    async def send_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                await connection.send_text(message)
    
    async def broadcast(self, message: str):
        for client_id in self.active_connections:
            await self.send_message(message, client_id)

manager = ConnectionManager()

@websocket("/{client_id:str}") # Updated decorator and path parameter type
async def websocket_endpoint_handler(socket: WebSocket, client_id: str) -> None: # Renamed function, websocket to socket, added return type
    await manager.connect(socket, client_id)
    try:
        while True:
            data = await socket.receive_text()
            # Process received data
            try:
                message = json.loads(data)
                # Handle different message types
                if message.get("type") == "ping":
                    await socket.send_text(json.dumps({"type": "pong"}))
                else:
                    # Echo back for now
                    await socket.send_text(data)
            except json.JSONDecodeError:
                await socket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))
    except WebSocketDisconnect:
        manager.disconnect(socket, client_id)

# Function to notify clients about new data or processing results
async def notify_clients(event_type: str, data: dict, client_id: Optional[str] = None) -> None: # Added Optional and return type
    message = json.dumps({
        "type": event_type,
        "data": data
    })
    
    if client_id:
        await manager.send_message(message, client_id)
    else:
        await manager.broadcast(message)

websocket_router = Router(path="/ws", route_handlers=[websocket_endpoint_handler])
