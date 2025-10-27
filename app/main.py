from fastapi import FastAPI

app = FastAPI(title="InkBoard", version="0.1.0")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "InkBoard is running smoothly!"}