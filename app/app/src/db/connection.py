import datetime
import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column


SQLALCHEMY_DATABASE_URL = os.environ.get("DB_URL", "postgresql+psycopg://exchange:df456Sdb34@0.0.0.0:6543/market")
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True, pool_size=20)
Base = declarative_base()

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session


class Mapper(Base):
    __tablename__ = 'mapper'
    # cg_id, exchange - must be unique together

    id: Mapped[int] = mapped_column(primary_key=True)
    cg_id: Mapped[str] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(primary_key=True)
    symbol: Mapped[str]
    update: Mapped[datetime.datetime]


class Volume(Base):
    __tablename__ = 'last_volumes'

    id: Mapped[int] = mapped_column(primary_key=True)
    cg_id: Mapped[str] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(primary_key=True)
    price: Mapped[float]
    volume: Mapped[float]
    update: Mapped[datetime.datetime]
