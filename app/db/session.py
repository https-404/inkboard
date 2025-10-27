from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(str(settings.DATABASE_URL), echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
