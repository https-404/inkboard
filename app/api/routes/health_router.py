from fastapi import APIRouter, Depends
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.deps import get_db

health_router = APIRouter(prefix="/health", tags=["Health"])

@health_router.get("/")
async def health_check():
    return {"status": "ok",
            "message": f"Application ({settings.APP_NAME}) version {settings.APP_VERSION} is running smoothly!"
            }

@health_router.get("/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {"status": "ok"}

