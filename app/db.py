from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import logging

# Control SQLAlchemy logging via settings
if not settings.log_sql_queries:
    # Suppress SQLAlchemy's verbose logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

engine = create_async_engine(
    settings.database_url, 
    echo=settings.log_sql_queries  # Only show SQL when explicitly enabled
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session

