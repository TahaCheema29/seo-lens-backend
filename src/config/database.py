from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.config.settings import settings

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug if hasattr(settings, 'debug') else False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """
    Create database tables directly.
    
    NOTE: For production, use Alembic migrations instead:
        - Run: make init-db
        - Or: python -m scripts.migrate migrate
    
    This function is for development convenience only.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)