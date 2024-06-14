import asyncio

import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange


class alterdice(BaseExchange):
    """
        docs: https://github.com/hyperevo/Atomars-alterdice-API/blob/master/atom_alter_API/api.py  no better docs(
    """
    def __init__(self):
        self.id = 'alterdice'
        self.cg_id = "alterdice"
        self.full_name = "AlterDice"
        self.base_url = "https://api.alterdice.com/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        result = {}
        for pair, ccxt_symbol in self.markets.items():
            data = await self.fetch_data(self.base_url + f'v1/public/ticker?pair={pair}')
            result.update(self.normalize_data(data))

        return result

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            return self.markets.get(symbols)
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        ticker = data.get('data', {})
        symbol = self._convert_symbol_to_ccxt(ticker.get('pair'))
        normalized_data[symbol] = {
            "last": float(ticker.get("last", 0)),
            "baseVolume": float(ticker.get("volume_24H", 0)),
            "quoteVolume": 0,
        }
        return normalized_data

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "v1/public/symbols")
        for symbol in data.get("data", []):
            self.markets[symbol.get("pair")] = symbol.get("base", "") + "/" + symbol.get("quote", "")

    async def close(self):
        pass  # stub, not really needed

