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
    await bot.chat_endpoint(websocket)

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Add this for Vercel - use Mangum class, not adapter module
handler = Mangum(app)

if __name__ == "__main__":
    # Use localhost with port 8080
    uvicorn.run("main:app", host="localhost", port=8080, reload=True)