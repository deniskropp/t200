import pytest
import asyncio
from src.core.db.session import engine, create_tables
from src.core.db.models import Base
from src.shared.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    """Setup database schema once for the session."""
    # Ensure using the test DB
    print(f"\nUsing DB URL: {settings.DATABASE_URL}")
    await create_tables()
    yield
    # Optional: cleanup
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncSession:
    """Provides a fresh database session for a test."""
    # Transactional rollback could be implemented here for speed
    # For now, just a session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
