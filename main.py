import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from bot import DoctorSnowLeopardBot

app = FastAPI()

# Create bot instance
bot = DoctorSnowLeopardBot()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add the bot's chat endpoint
app.add_api_websocket_route("/chat", bot.chat_endpoint)

@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Add this for Vercel
from mangum import Adapter
handler = Adapter(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 