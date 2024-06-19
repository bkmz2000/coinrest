import asyncio
import time
from dataclasses import dataclass
from ccxt.async_support.base.exchange import BaseExchange
import datetime
from pydantic import BaseModel, ConfigDict

@dataclass
class Match:
    cg_id: str
    exchange: BaseExchange
    symbol: str


class BaseMapper(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    ccxt_name: str
    symbol: str


class LastLost(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    price_usd: float | None
    volume_usd: float | None
    last_update: datetime.datetime


class TickerToMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exchange_id: int
    base: str
    price_usd: float


class TickerSimple(BaseModel):
    cg_id: str
    price_usd: float | None
    volume_usd: float


class TickerMatched(BaseModel):
    exchange_id: int
    base_cg: str
    symbol: str


class Last(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str | None
    price_usd: float | None
    volume_usd: float | None

    price_btc: float | None
    volume_btc: float | None


class UpdateEventFrom(BaseModel):
    event: str
    createdAt: datetime.datetime
    model: str
    entry: dict


class UpdateEventTo(BaseModel):
    ticker_num: int
    last_update: str

@dataclass
class Coin:
    exchange: str = ''
    volume: float = 0
    price: float = 0


class QuoteRate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    currency: str
    rate: float
    update_at: datetime.datetime | None = None


class CoinWithPrice(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    price_usd: float


class CoinWithPriceAndDate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str | None
    price_usd: float
    created_at: int | None

class LastCoinWithSymbol(BaseModel):
    cg_id: str
    base: str
    price_usd: float

@dataclass
class ActualCoinIn:
    cg_id: str


@dataclass
class HistoricalDT:
    cg_id: str
    price_usd: float
    timestamp: int
    volume_usd: float | None = None

class NotActiveExchange(Exception):
    ...

@dataclass
class CreateExchange:
    ccxt_name: str
    full_name: str
    cg_identifier: str


class OrderBookCoin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    symbol: str


class OrderBook(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    base: str
    quote: str
    exchange: str
    bids: list
    asks: list

class OrderBookFromDB(OrderBook):
    last_price: float


class SocketUpdated(BaseModel):
    cg_id: str
    exchange: str
    price_usd: float
    updated_at: datetime.datetime


class FiatRate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    currency: str
    rate: float
    updated_at: datetime.datetime


def repeat_with_timeout(timeout: int):
    """
        Restart func every {timeout} seconds
        If task working more than {timeout} seconds, sleep only 2 secs
    """
    def repeat_forever(func):
        async def wrapper(*args, **kwargs):
            while True:
                start_time = time.time()
                await func(*args, **kwargs)
                end_time = time.time() - start_time
                to_sleep = timeout - end_time
                if to_sleep < 0:
                    to_sleep = 2
                await asyncio.sleep(to_sleep)
        return wrapper
    return repeat_forever
