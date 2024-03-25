import aiohttp
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


class nami_exchange:
    """
        docs: https://namiexchange.github.io/docs/#get-24hr-ticker-price
    """
    def __init__(self):
        self.id = 'nami_exchange'
        self.base_url = "https://nami.exchange/api/v1.0/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'market/summaries')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, row: dict) -> str:
        base_symbol = row.get('exchange_currency')
        quote_symbol = row.get('base_currency')
        if base_symbol and quote_symbol:
            return f'{base_symbol}/{quote_symbol}'

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
        tickers = data['data']
        for row in tickers:
            symbol = self._convert_symbol_to_ccxt(row)
            if not symbol:
                continue
            normalized_data[symbol] = {
                "last": float(row.get("last_price", 0)),
                "baseVolume": float(row.get("total_exchange_volume", 0)),
                "quoteVolume": 0
            }
        return normalized_data

    async def load_markets(self):
        pass

    async def close(self):
        pass
