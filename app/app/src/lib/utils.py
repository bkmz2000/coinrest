from collections import defaultdict
from dataclasses import dataclass, field
from ccxt.async_support.base.exchange import BaseExchange
import datetime
from pydantic import BaseModel, ConfigDict


@dataclass
class GeckoMarkets:
    symbol: str
    exchange: BaseExchange


class BaseMapper(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    exchange: str
    symbol: str


class Mapper(BaseMapper):
    id: int
    update: datetime.datetime


class ChartResponse(BaseModel):
    prices: list[tuple[int, float]]
    exchange: str


class BaseLastVolume(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cg_id: str
    volume: float
    price: float


class LastVolume(BaseLastVolume):
    id: int
    update: datetime.datetime


@dataclass
class Coin:
    volume: float = 0
    price: float = 0

class CoinResponse(BaseModel):
    usd: float
    usd_24_vol: float
