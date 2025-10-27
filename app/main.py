from fastapi import Depends, FastAPI
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.deps import get_db

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": f"{settings.APP_NAME} : Version {settings.APP_VERSION} is running smoothly!"}

@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}