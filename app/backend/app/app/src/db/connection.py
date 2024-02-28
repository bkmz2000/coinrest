import datetime
import os
from typing import List

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

SQLALCHEMY_DATABASE_URL = os.environ.get("DB_URL", "postgresql+psycopg://exchange:df456Sdb34@0.0.0.0:6543/market")
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True, pool_size=200, max_overflow=50)
Base = declarative_base()

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session


class Mapper(Base):
    __tablename__ = 'mapper'
    # cg_id, exchange - must be unique together

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cg_id: Mapped[str] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(primary_key=True)
    symbol: Mapped[str]
    update: Mapped[datetime.datetime]


class Volume(Base):
    __tablename__ = 'last_volumes'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cg_id: Mapped[str] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(primary_key=True)
    price: Mapped[float]
    volume: Mapped[float]
    update: Mapped[datetime.datetime]


class QuoteMapper(Base):
    __tablename__ = 'quote_converter'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    currency: Mapped[str] = mapped_column(primary_key=True, unique=True)
    rate: Mapped[float]
    update_at: Mapped[datetime.datetime]


class Exchange(Base):
    __tablename__ = 'exchange'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    ticker: Mapped[List["Ticker"]] = relationship(back_populates="exchange", cascade="all, delete", passive_deletes=True)
    trust: Mapped[int]


class Ticker(Base):
    __tablename__ = 'ticker'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchange.id", ondelete="CASCADE"), nullable=False)
    exchange: Mapped["Exchange"] = relationship(back_populates="ticker")
    base: Mapped[str]
    base_cg: Mapped[str]
    quote: Mapped[str]
    quote_cg: Mapped[str]
    price: Mapped[float]
    price_usd: Mapped[float]
    base_volume: Mapped[float]
    quote_volume: Mapped[float]
    volume_usd: Mapped[float]
    last_update: Mapped[int]

    __table_args__ = (UniqueConstraint("exchange_id", "base", "quote", name="unique_ticker"),)
