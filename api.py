from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from Dr. Snow Paws API!"}

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Handler for serverless function
handler = Mangum(app) 