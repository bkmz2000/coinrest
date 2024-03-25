import datetime
import os
from typing import List

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

SQLALCHEMY_DATABASE_URL = os.environ.get("DB_URL", "postgresql+psycopg://exchange:df456Sdb34@0.0.0.0:6543/new_market")
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True, pool_size=200, max_overflow=50)
Base = declarative_base()

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session
