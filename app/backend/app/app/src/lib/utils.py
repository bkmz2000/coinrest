import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from ccxt.async_support.base.exchange import BaseExchange
import datetime
from pydantic import BaseModel, ConfigDict
from loguru import logger as lg


@dataclass
class GeckoMarkets:
    symbol: str
    exchange: BaseExchange


class BaseMapper(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    ccxt_name: str
    symbol: str

class ChartResponse(BaseModel):
    prices: list[tuple[int, float]]
    exchange: str


class Last(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str | None
    price_usd: float | None
    volume_usd: float | None

    price_btc: float | None
    volume_btc: float | None


@dataclass
class Coin:
    exchange: str = ''
    volume: float = 0
    price: float = 0


class CoinResponse(BaseModel):
    usd: float | None
    usd_24h_vol: float | None

    btc: float | None
    btc_24h_vol: float | None


class QuoteRate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    currency: str
    rate: float
    update_at: datetime.datetime | None = None


def sleeping(func):
    """
        Restart func every 5 minutes/
        If task working more than 5 min, sleep only 2 secs
    """
    max_time = 300

    async def wrapper(*args, **kwargs):
        while True:
            start_time = time.time()
            await func(*args, **kwargs)
            end_time = time.time() - start_time
            to_sleep = max_time - end_time
            if to_sleep < 0:
                to_sleep = 2
            await asyncio.sleep(to_sleep)

    return wrapper