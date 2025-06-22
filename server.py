import os
from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import logging
import json
from loguru import logger
from bot import DoctorSnowLeopardBot
import base64
import tempfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create bot instance
bot = DoctorSnowLeopardBot()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

logger = logging.getLogger(__name__)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive message
            message = await websocket.receive_text()
            logger.info(f"Received message: {message}")
            
            try:
                # Handle heartbeat messages
                if message.strip() == '{"type":"heartbeat"}':
                    await websocket.send_json({"type": "heartbeat"})
                    continue
                
                # Generate response using the bot
                response = await bot.generate_response(message)
                
                # Send response to client
                await websocket.send_json(response)
                logger.info("Response sent successfully")
                
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                error_response = {
                    "text": "*adjusts glasses* Oh my! I got a little tangled in my medical notes. Could you please repeat that? 🐾",
                    "audio": None,
                    "emotion": "caring"
                }
                await websocket.send_json(error_response)
                
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/transcribe")
async def transcribe_audio(request: Request):
    """Endpoint to transcribe audio using Whisper API"""
    try:
        # Get the audio data from the request
        data = await request.json()
        audio_base64 = data.get("audio")
        
        if not audio_base64:
            raise HTTPException(status_code=400, detail="No audio data provided")
            
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_base64.split(",")[1])
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name
        
        try:
            # Transcribe using Whisper API
            with open(temp_path, "rb") as audio_file:
                transcript = await bot.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            return JSONResponse({
                "success": True,
                "text": transcript
            })
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("FAST_API_PORT", "7860"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    print(f"To interact with Doctor Snow Leopard, visit http://{host}:{port}/")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=reload,
    )
