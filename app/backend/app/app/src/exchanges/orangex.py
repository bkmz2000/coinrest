import aiohttp
from src.exchanges.base import BaseExchange
from loguru import logger as lg


class orangex(BaseExchange):
    """
        docs: https://openapi-docs.orangex.com/#spot-summary
    """
    def __init__(self):
        self.id = 'orangex'
        self.cg_id = "orangex"
        self.full_name = "OrangeX"
        self.base_url = "https://api.orangex.com/api/v1/public/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'cmc_spot_summary')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str | list[str]) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("-", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    async def fetch_data(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception(resp)
        return data

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        result = data.get("result", [])
        for row in result:
            symbol = self._convert_symbol_to_ccxt(row.get("trading_pairs"))
            normalized_data[symbol] = {
                "last": float(row.get("last_price", 0)),
                "baseVolume": float(row.get("base_volume", 0)),
                "quoteVolume": float(row.get("quote_volume", 0))
            }
        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass
