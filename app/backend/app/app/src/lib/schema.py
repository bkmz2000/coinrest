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


class TopExchangeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    trust_score: int
    volume_24h: float


class StrapiMarket(BaseModel):
    ccxt_name: str
    cg_identifier: str | None
    centralized: bool | None
    trust_score: int | None
    logo: str | None
    is_active: bool | None
    full_name: str | None


class MarketMapping(BaseModel):
    exchange_id: str
    symbol: str
    cg_id: str
    updated_at: datetime.datetime


class CoinResponse(BaseModel):
    id: int
    exchange: str
    logo: str | None
    pair: str
    price: float
    volume_24h: float
    exchange_type: Literal['ALL', 'CEX', 'DEX']
    trading_type: Literal['Spot', 'Perpetual', 'Futures']


class PriceResponse(BaseModel):
    usd: float | None
    usd_24h_vol: float | None

    btc: float | None
    btc_24h_vol: float | None


class MarketResponse(BaseModel):
    coins: list[CoinResponse]
    total: int
    quotes: list[str]


class HistoricalRequest(BaseModel):
    cg_id: str
    timeframe: Literal['5m', '1h', '1d']
    stamps: list[int]


class NewHistoricalRequest(BaseModel):
    hdr_id: str
    timeframe: Literal['5m', '1h', '1d']
    stamp: int


class HistoricalResponse(BaseModel):
    hdr_id: str
    stamp: int
    price: float
    price_btc: float | None = None
    volume: float | None = None
    volume_btc: float | None = None


class NewCoinResponse(BaseModel):
    cg_id: str | None
    created_at: int


class NewTickerResponse(BaseModel):
    base: str
    quote: str
    price_usd: float
    on_create_id: str
    created_at: int
    exchange: str
    new_for_market: bool
    new_for_exchange: bool

class Bid(BaseModel):
    price: float
    qty: float


class Ask(BaseModel):
    price: float
    qty: float


class DepthChart(BaseModel):
    bids: list[Bid]
    asks: list[Ask]


class MarketDepthResponse(BaseModel):
    exchange: str
    symbol: str
    coin_id: str
    bids_volume: float
    asks_volume: float
    depth_chart: DepthChart


class MappedCoinResponse(BaseModel):
    hdr_id: str
    base: str

class ExchangePair(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base: str
    quote: str

    price: float
    volume: float

class PairsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exchange_id: str
    pairs: list[ExchangePair]

class PercentagePair(BaseModel):
    pair: str
    volume: float 
    percentage: float


class TopPairsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exchange_id: str
    pairs: list[PercentagePair]

class CoinPercentage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    coin: str
    volume: float
    percentage: float

class TopCoinsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exchange_id: str
    coins: list[CoinPercentage]


class ChartEntry(BaseModel):
    timestamp: int
    volume: float


class ExchangeChartResponse(BaseModel):
    exchange_id: str
    period: Literal['24h', '7d', '14d', '1M', '3M', '1Y']
    currency: str
    data: list[ChartEntry]
