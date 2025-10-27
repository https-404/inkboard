from fastapi import FastAPI
from app.core.config import settings
from app.api.router import api_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.include_router(api_router)