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
