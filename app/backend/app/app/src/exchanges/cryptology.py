import asyncio
from src.exchanges.base import BaseExchange
from loguru import logger as lg


class cryptology(BaseExchange):
    """
        docs: https://docs.cryptology.com/#list-available-trading-pairs
    """
    def __init__(self):
        self.id = 'cryptology'
        self.cg_id = "cryptology"
        self.full_name = "Cryptology"
        self.base_url = "https://api.cryptology.com/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        raw_data = {}
        for pair in self.markets:
            last_price_data = await self.fetch_data(self.base_url + f'v1/public/get-trades?trade_pair={pair}&limit=1')
            await asyncio.sleep(1)
            volume_data = await self.fetch_data(self.base_url + f'v1/public/get-24hrs-stat?trade_pair={pair}')
            if last_price_data.get("status") == "OK" and volume_data.get("status") == "OK":
                raw_data[pair] = {
                    "price": last_price_data.get("data", [{}])[0].get("price", 0),
                    "volume": volume_data.get("data", {}).get("base_volume", 0),
                }
            else:
                await asyncio.sleep(1)
            await asyncio.sleep(1)
        return self.normalize_data(raw_data)

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            return self.markets.get(symbols)
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        for symbol, prop in data.items():
            symbol = self._convert_symbol_to_ccxt(symbol)
            normalized_data[symbol] = {
                "last": float(prop.get("price", 0)),
                "baseVolume": float(prop.get("volume", 0)),
                "quoteVolume": 0,
            }
        return normalized_data

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "v1/public/get-trade-pairs")
        if data.get("status") != "OK":
            return None
        data = data['data']
        for pair in data:
            self.markets[pair["trade_pair"]] = pair["base_currency"] + "/" + pair["quoted_currency"]

    async def close(self):
        pass  # stub, not really needed
