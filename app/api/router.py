from fastapi import APIRouter
from app.api.routes.user_router import user_router
from app.api.routes.health_router import health_router
from app.api.routes.auth_router import auth_router

api_router = APIRouter(prefix="/api/v1")


#Test router
from app.api.routes.test_router import test_router
api_router.include_router(test_router)

# Include routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(user_router)

