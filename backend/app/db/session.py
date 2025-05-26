from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import settings

# Create the async engine
# echo=True is for logging SQL statements, can be removed in production
# future=True enables the newer SQLAlchemy 2.0 style execution
engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)


async def get_session() -> AsyncSession:
    """
    FastAPI dependency to get an async database session.
    """
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


async def create_db_and_tables():
    """
    Creates all database tables defined by SQLModel metadata.
    Should be called on application startup or for initial setup.
    Alembic will handle migrations for existing databases.
    """
    # Import all models here so that SQLModel.metadata knows about them
    # This is crucial for create_all to work correctly.
    # Adjust the import path if your models are elsewhere.
    from backend.app.db import models  # noqa

    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all) # Use with caution: drops all tables
        await conn.run_sync(SQLModel.metadata.create_all)

# Optional: A function to initialize the database, can be called from main.py
# async def init_db():
#     await create_db_and_tables()
#
# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(init_db())
