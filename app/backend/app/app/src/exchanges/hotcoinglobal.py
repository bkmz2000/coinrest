import aiohttp
# from aiohttp_proxy import ProxyConnector, ProxyType
from loguru import logger as lg
from src.exchanges.base import BaseExchange

class hotcoinglobal(BaseExchange):
    """
        docs: https://hotcoinex.github.io/en/spot/market.html
    """
    def __init__(self):
        self.id = 'hotcoinglobal'
        self.cg_id = "hotcoin_global"
        self.full_name = "Hotcoin Global"
        self.base_url = "https://api.hotcoinfin.com/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'v1/market/ticker')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str | list[str]) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/").upper()
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    async def fetch_data(self, url: str):
        # connector = ProxyConnector(
        #     proxy_type=ProxyType.SOCKS5,
        #     host='127.0.0.1',
        #     port=9999,
        #     rdns=True
        # )
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception(resp)
        return data

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        tickers = data.get("ticker", [])
        for row in tickers:
            symbol = self._convert_symbol_to_ccxt(row.get("symbol"))
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
