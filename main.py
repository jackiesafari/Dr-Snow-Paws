import os
import uvicorn
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from bot import DoctorSnowLeopardBot
from mangum import Mangum

app = FastAPI()

# Create bot instance
bot = DoctorSnowLeopardBot()

# Determine the static directory path
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Mount static files with absolute path
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add the bot's chat endpoint
@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    await bot.chat_endpoint(websocket)

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))

# Configure Mangum with specific options for Vercel
handler = Mangum(app, lifespan="off")

if __name__ == "__main__":
    # Use localhost with port 8080
    uvicorn.run("main:app", host="localhost", port=8080, reload=True)