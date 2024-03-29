import datetime
from dataclasses import dataclass
from typing import Literal

from numpy import array
from pydantic import BaseModel, ConfigDict

@dataclass
class TickerInfo:
    exchange_id: str
    base: str
    base_cg: str | None
    quote: str
    quote_cg: str | None
    price: float
    price_usd: float
    base_volume: float
    quote_volume: float
    volume_usd: float

class CoinInput:
    price: array = array([])
    volume: array = array([])

class CoinOutput(BaseModel):
    cg_id: str
    price_usd: float
    volume_usd: float
    price_btc: float | None
    volume_btc: float | None

class TickerSimple(BaseModel):
    cg_id: str
    price_usd: float | None
    volume_usd: float


class TickerToMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exchange_id: int
    base: str
    price_usd: float


class TickerMatched(BaseModel):
    exchange_id: int
    base_cg: str
    symbol: str


class TickerResponse(BaseModel):
    name: str | None
    base: str
    base_cg: str | None
    quote: str
    price_usd: float
    volume_usd: float
    last_update: int

class ExchangeNameResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str


class ExchangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cg_identifier: str


class StrapiMarket(BaseModel):
    name: str
    trust_score: int | None
    logo: str | None


class MarketMapping(BaseModel):
    exchange_id: str
    symbol: str
    cg_id: str
    updated_at: datetime.datetime


class UpdateEventFrom(BaseModel):
    event: str
    createdAt: datetime.datetime
    model: str
    entry: dict


class UpdateEventTo(BaseModel):
    ticker_num: int
    last_update: str


class CoinResponse(BaseModel):
    id: int
    exchange: str
    logo: str | None
    pair: str
    price: float
    volume_24h: float
    exchange_type: Literal['ALL', 'CEX', 'DEX']
    trading_type: Literal['Spot', 'Perpetual', 'Futures']


class MarketResponse(BaseModel):
    coins: list[CoinResponse]
    total: int
    quotes: list[str]


class HistoricalRequest(BaseModel):
    cg_id: str
    timeframe: Literal['5m', '1h', '1d']
    stamps: list[int]


class HistoricalResponse(BaseModel):
    cg_id: str
    stamp: int
    price: float

# {
#   "event": "entry.update",
#   "createdAt": "2020-01-10T08:58:26.563Z",
#   "model": "address",
#   "entry": {
#     "id": 1,
#     "geolocation": {},
#     "city": "Paris",
#     "postal_code": null,
#     "category": null,
#     "full_name": "Paris",
#     "createdAt": "2020-01-10T08:47:36.264Z",
#     "updatedAt": "2020-01-10T08:58:26.210Z",
#     "cover": null,
#     "images": []
#   }
# }