from fastapi import APIRouter
from app.api.routes.health_router import health_router
from app.api.routes.auth_router import auth_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)
api_router.include_router(auth_router)

