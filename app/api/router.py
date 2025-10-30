from fastapi import APIRouter
from app.api.routes.user_router import user_router
from app.api.routes.health_router import health_router
from app.api.routes.auth_router import auth_router
from app.api.routes.media_router import media_router
from app.api.routes.search_router import search_router
from app.api.routes.article_router import article_router
from app.api.routes.follow_router import follow_router
from app.api.routes.home_router import home_router
from app.api.routes.comment_router import comment_router

api_router = APIRouter(prefix="/api/v1")


#Test router
from app.api.routes.test_router import test_router
api_router.include_router(test_router)

# Include routers
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(media_router)
api_router.include_router(search_router)
api_router.include_router(article_router)
api_router.include_router(follow_router)
api_router.include_router(home_router)
api_router.include_router(comment_router)

