import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Dr. Snow Paws API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("simple_app:app", host="0.0.0.0", port=port) 