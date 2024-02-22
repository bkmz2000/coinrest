from dataclasses import dataclass
from pydantic  import BaseModel, ConfigDict

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

class TickerToMatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    base: str
    price_usd: float

class TickerMatched(BaseModel):
    id: int
    base_cg: str
