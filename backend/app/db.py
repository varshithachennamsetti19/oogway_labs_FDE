"""
Database Connection & Session Management
Supports PostgreSQL with pgvector, plus SQLite fallback for offline unit tests.
"""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text

from backend.app.config import get_settings

logger = logging.getLogger("lenny_growth.db")
settings = get_settings()

db_url = settings.DATABASE_URL
is_sqlite = db_url.startswith("sqlite")

# Create Async Engine
engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    future=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def init_db():
    """Initializes database extensions (pgvector) and creates all tables."""
    try:
        async with engine.begin() as conn:
            if not is_sqlite:
                logger.info("Initializing pgvector extension...")
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            
            logger.info("Creating database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialization completed successfully.")
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        # Allow server to start even if DB is not ready yet; health check will surface it
        raise e


async def get_db_session():
    """FastAPI Dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
