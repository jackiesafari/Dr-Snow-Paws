import os
import uvicorn
import logging
from fastapi import FastAPI, WebSocket, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from bot import DoctorSnowLeopardBot
from mangum import Mangum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)},
    )

# Create bot instance
try:
    bot = DoctorSnowLeopardBot()
except Exception as e:
    logger.error(f"Error initializing bot: {str(e)}", exc_info=True)
    bot = None

# Determine the static directory path
static_dir = os.path.join(os.path.dirname(__file__), "static")

# Mount static files with absolute path
try:
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
except Exception as e:
    logger.error(f"Error mounting static files: {str(e)}", exc_info=True)

# Add the bot's chat endpoint
@app.websocket("/chat")
async def chat_endpoint(websocket: WebSocket):
    try:
        if bot is None:
            await websocket.accept()
            await websocket.send_text("Bot initialization failed. Please check server logs.")
            await websocket.close()
        else:
            await bot.chat_endpoint(websocket)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        try:
            if websocket.client_state.CONNECTED:
                await websocket.send_text(f"An error occurred: {str(e)}")
                await websocket.close()
        except:
            pass

@app.get("/")
async def root():
    try:
        return FileResponse(os.path.join(static_dir, "index.html"))
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"message": "Error serving index page", "detail": str(e)},
        )

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# For serverless environments (like Vercel)
handler = Mangum(app)

if __name__ == "__main__":
    # Get port from environment variable for Railway
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)