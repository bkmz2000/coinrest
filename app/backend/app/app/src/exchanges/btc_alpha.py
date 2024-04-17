import os

import aiohttp
from aiohttp_proxy import ProxyConnector, ProxyType
from loguru import logger as lg
from src.exchanges.base import BaseExchange

class btc_alpha(BaseExchange):
    """
        docs: https://btc-alpha.github.io/api-docs/#list-all-pairs
    """
    def __init__(self):
        self.id = 'btc_alpha'
        self.cg_id = "btc_alpha"
        self.full_name = "BTC-Alpha"
        self.base_url = "https://btc-alpha.com/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'api/v1/ticker/')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str | list[str]) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/").upper()
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    async def fetch_data(self, url: str):
        connector = aiohttp.TCPConnector()

        # connector = ProxyConnector(
        #     proxy_type=ProxyType.SOCKS5,
        #     host='127.0.0.1',
        #     port=9999,
        #     rdns=True)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception(resp)
        return data

    def normalize_data(self, data: list) -> dict:
        normalized_data = {}
        for row in data:
            symbol = self._convert_symbol_to_ccxt(row.get("pair"))
            normalized_data[symbol] = {
                "last": float(row.get("last", 0)),
                "baseVolume": float(row.get("vol", 0)),
                "quoteVolume": 0
            }
        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass
