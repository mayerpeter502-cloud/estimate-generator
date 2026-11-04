import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Получаем URL базы данных из .env или используем значение по умолчанию
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./estimates.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Этот Base будет использоваться во всех моделях!
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session