from fastapi import FastAPI
from os import getenv
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title=getenv("APP_NAME", "InkBoard"), version=getenv("APP_VERSION", "0.1.0"))

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": f"{getenv('APP_NAME')} : Version {getenv('APP_VERSION')} is running smoothly!"}