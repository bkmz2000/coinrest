import datetime
from typing import List

from sqlalchemy import ForeignKey, UniqueConstraint, func, SMALLINT, BIGINT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import NUMERIC, TEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()


class QuoteMapper(Base):
    __tablename__ = 'quote_converter'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    currency: Mapped[str] = mapped_column(TEXT, primary_key=True, unique=True)
    rate: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    update_at: Mapped[datetime.datetime] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("currency", name="currency"),)

class Exchange(Base):
    __tablename__ = 'exchange'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ccxt_name: Mapped[str] = mapped_column(TEXT, nullable=True)
    cg_identifier: Mapped[str] = mapped_column(TEXT, nullable=True)
    full_name: Mapped[str] = mapped_column(TEXT, nullable=True)
    trust_score: Mapped[int] = mapped_column(SMALLINT, nullable=True)
    centralized: Mapped[bool] = mapped_column(nullable=True)
    logo: Mapped[str] = mapped_column(TEXT, nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=True, default=True)

    ticker: Mapped[List["Ticker"]] = relationship(back_populates="exchange", cascade="all, delete",
                                                  passive_deletes=True)
    exchange_tickers_mapper: Mapped[List["ExchangeMapper"]] = relationship(back_populates="exchange", cascade="all, delete",
                                                          passive_deletes=True)

    __table_args__ = (UniqueConstraint("ccxt_name", name="unique_exchange_name"),)

    def __str__(self):
        return self.ccxt_name


class Ticker(Base):
    __tablename__ = 'ticker'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(SMALLINT, ForeignKey("exchange.id", ondelete="CASCADE"), nullable=True)
    exchange: Mapped["Exchange"] = relationship(back_populates="ticker")
    base: Mapped[str] = mapped_column(TEXT, nullable=True)
    base_cg: Mapped[str] = mapped_column(TEXT, nullable=True)
    quote: Mapped[str] = mapped_column(TEXT, nullable=True)
    quote_cg: Mapped[str] = mapped_column(TEXT, nullable=True)
    price: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    price_usd: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    base_volume: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    quote_volume: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    volume_usd: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    last_update: Mapped[int] = mapped_column(nullable=True)

    __table_args__ = (UniqueConstraint("exchange_id", "base", "quote", name="unique_ticker"),)

    def __str__(self):
        return f"{self.base}/{self.quote}"


class ExchangeMapper(Base):
    __tablename__ = 'exchange_tickers_mapper'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(SMALLINT, ForeignKey("exchange.id", ondelete="CASCADE"), nullable=True)
    exchange: Mapped["Exchange"] = relationship(back_populates="exchange_tickers_mapper")
    symbol: Mapped[str] = mapped_column(TEXT, nullable=True)
    cg_id: Mapped[str] = mapped_column(TEXT, nullable=True)
    updated_at: Mapped[datetime.datetime] = mapped_column(nullable=True, server_default=func.now())

    __table_args__ = (UniqueConstraint("exchange_id", "symbol", name="exchange_symbol_unique"),)


class LastValues(Base):
    __tablename__ = 'last'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cg_id: Mapped[str] = mapped_column(TEXT, unique=True, nullable=True)
    price_usd: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    price_btc: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    volume_usd: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    volume_btc: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    last_update: Mapped[datetime.datetime] = mapped_column(nullable=True, server_default=func.now())

    __table_args__ = (UniqueConstraint("cg_id", name="cg_id_unique"),)


class ActualCoingecko(Base):
    __tablename__ = 'actual_coingecko'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cg_id: Mapped[str] = mapped_column(TEXT, nullable=True)


class Historical(Base):
    __tablename__ = 'historical'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    cg_id: Mapped[str] = mapped_column(TEXT, nullable=True)
    price_usd: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    volume_usd: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    price_btc: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    volume_btc: Mapped[float] = mapped_column(NUMERIC, nullable=True)
    timestamp: Mapped[int] = mapped_column(BIGINT, nullable=True)

    __table_args__ = (UniqueConstraint("cg_id", "timestamp", name="gecko_stamp_unique"),)