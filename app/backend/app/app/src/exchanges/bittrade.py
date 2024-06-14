import asyncio

import aiohttp
from loguru import logger as lg
from src.exchanges.base import BaseExchange
from aiohttp_proxy import ProxyConnector, ProxyType


class bittrade(BaseExchange):
    """
        docs: https://api-doc.bittrade.co.jp/#rest-api
    """
    def __init__(self):
        self.id = 'bittrade'
        self.cg_id = "huobi_japan"
        self.full_name = "BitTrade"
        self.base_url = "https://api-cloud.bittrade.co.jp/"
        self.markets = {}

    async def fetch_data(self, url: str):
        """
        :param url: URL to fetch the data from exchange
        :return: raw data
        """
        # connector = ProxyConnector(
        #     proxy_type=ProxyType.SOCKS5,
        #     host='127.0.0.1',
        #     port=9999,
        #     ssl=True,
        # )
        # async with aiohttp.ClientSession(connector=connector) as session:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception(resp)
        return data

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'market/tickers')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.split('jpy')[0].upper() + "/JPY"
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        tickers = data.get('data', {})
        for ticker in tickers:
            symbol = self._convert_symbol_to_ccxt(ticker.get('symbol'))
            normalized_data[symbol] = {
                "last": float(ticker.get("close", 0)),
                "baseVolume": 0,
                "quoteVolume": float(ticker.get("vol", 0)),
            }
        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass  # stub, not really needed

