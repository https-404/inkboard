from fastapi import APIRouter
from app.api.routes.health_router import health_router

api_router = APIRouter()

api_router.include_router(health_router)
