import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from bot import DoctorSnowLeopardBot
from mangum import Mangum

app = FastAPI()

# Create bot instance
bot = DoctorSnowLeopardBot()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add the bot's chat endpoint
@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive message
            message = await websocket.receive_text()
            
            # Generate response
            response = await bot.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are Doctor Snow Leopard, a friendly pediatrician snow leopard who helps children feel comfortable in medical settings."},
                    {"role": "user", "content": message}
                ]
            )
            result = response.choices[0].message.content
            
            # Determine emotion
            emotion = "caring"
            if "happy" in result.lower() or "!" in result:
                emotion = "happy"
            elif "?" in result:
                emotion = "listening"
            
            # Generate speech (with error handling)
            try:
                audio_data = await bot.generate_speech(result)
                # Send response back with audio
                await websocket.send_json({
                    "text": result,
                    "emotion": emotion,
                    "audio": audio_data
                })
            except Exception as e:
                print(f"TTS Error: {e}")
                # Send response without audio if TTS fails
                await websocket.send_json({
                    "text": result,
                    "emotion": emotion
                })
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Add this for Vercel - use Mangum class, not adapter module
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 