from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.shared.config import settings

# Create the async engine with settings from the shared configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Configure the session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a database session for FastAPI requests."""
    async with AsyncSessionLocal() as session:
        yield session

async def create_tables() -> None:
    """Helper to create tables for development and testing."""
    from src.core.db.models import Base
    # We import models here to ensure they are registered with Base metadata
    import src.core.db.models # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
