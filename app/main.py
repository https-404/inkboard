from fastapi import FastAPI
from app.core.config import settings
from app.api.router import api_router
from app.middleware.jwt_middleware import JWTAuthMiddleware

app = FastAPI(title=settings.APP_NAME, 
              version=settings.APP_VERSION, 
              docs_url="/docs",      
              redoc_url="/redoc",    
              openapi_url="/openapi.json")

app.add_middleware(JWTAuthMiddleware)

app.include_router(api_router)