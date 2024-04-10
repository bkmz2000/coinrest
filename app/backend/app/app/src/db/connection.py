import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

SQLALCHEMY_DATABASE_URL = os.environ.get("DB_URL")
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, future=True, pool_size=200, max_overflow=50)

AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionFactory() as session:
        yield session
