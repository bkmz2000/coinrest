import datetime
from typing import List

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

Base = declarative_base()


class QuoteMapper(Base):
    __tablename__ = 'quote_converter'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    currency: Mapped[str] = mapped_column(primary_key=True, unique=True)
    rate: Mapped[float]
    update_at: Mapped[datetime.datetime]


class Exchange(Base):
    __tablename__ = 'exchange'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ccxt_name: Mapped[str]
    cg_identifier: Mapped[str]
    full_name: Mapped[str]
    trust_score: Mapped[int]
    centralized: Mapped[bool]
    logo: Mapped[str]

    ticker: Mapped[List["Ticker"]] = relationship(back_populates="exchange", cascade="all, delete",
                                                  passive_deletes=True)
    exchange_tickers_mapper: Mapped[List["ExchangeMapper"]] = relationship(back_populates="exchange", cascade="all, delete",
                                                          passive_deletes=True)

    def __str__(self):
        return self.ccxt_name


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

    def __str__(self):
        return f"{self.base}/{self.quote}"


class ExchangeMapper(Base):
    __tablename__ = 'exchange_tickers_mapper'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchange.id", ondelete="CASCADE"), nullable=False)
    exchange: Mapped["Exchange"] = relationship(back_populates="exchange_tickers_mapper")
    symbol: Mapped[str]
    cg_id: Mapped[str] = mapped_column(primary_key=True)
    updated_at: Mapped[datetime.datetime]

    __table_args__ = (UniqueConstraint("exchange_id", "symbol", name="exchange_symbol_unique"),)


class LastValues(Base):
    __tablename__ = 'last'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cg_id: Mapped[str] = mapped_column(unique=True)
    price_usd: Mapped[float]
    price_btc: Mapped[float]
    volume_usd: Mapped[float]
    volume_btc: Mapped[float]
    last_update: Mapped[datetime.datetime]

    __table_args__ = (UniqueConstraint("cg_id", name="cg_id_unique"),)


class ActualCoingecko(Base):
    __tablename__ = 'actual_coingecko'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cg_id: Mapped[str]


class Historical(Base):
    __tablename__ = 'historical'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cg_id: Mapped[str]
    price_usd: Mapped[float]
    volume_usd: Mapped[float]
    price_btc: Mapped[float]
    volume_btc: Mapped[float]
    timestamp: Mapped[int]

    __table_args__ = (UniqueConstraint("cg_id", "timestamp", name="gecko_stamp_unique"),)