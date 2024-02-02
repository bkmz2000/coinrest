import datetime
import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column


SQLALCHEMY_DATABASE_URL = os.environ["DB_URL"]
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)
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
