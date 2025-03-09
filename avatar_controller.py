from fastapi import FastAPI, WebSocket
from typing import Dict
import json

class AvatarController:
    def __init__(self):
        self.app = FastAPI()
        self.active_connections: Dict[str, WebSocket] = {}
        
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            await self.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_text()
                    await self.handle_message(client_id, data)
            except:
                await self.disconnect(client_id)
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
    
    async def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
    
    async def handle_message(self, client_id: str, data: str):
        # Process incoming messages from the client
        message_data = json.loads(data)
        # Handle different message types
        if message_data.get("type") == "avatar_request":
            await self.update_avatar_state(client_id, message_data.get("data", {}))

    async def update_avatar_state(self, client_id: str, state: dict):
        """Update avatar expression and position"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json({
                "type": "avatar_update",
                "data": state
            })

    async def sync_with_audio(self, client_id: str, audio_data: bytes):
        """Sync avatar lip movement with audio"""
        # Process audio data for lip sync
        phonemes = self.analyze_audio(audio_data)
        await self.update_avatar_state(client_id, {
            "lipSync": phonemes,
            "isPlaying": True
        })
    
    def analyze_audio(self, audio_data: bytes):
        """Analyze audio to extract phonemes for lip sync"""
        # This is a placeholder for actual audio analysis
        # In a real implementation, you would use a library to extract phonemes
        return ["a", "o", "e"]  # Example phonemes