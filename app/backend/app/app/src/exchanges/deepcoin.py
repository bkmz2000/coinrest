import aiohttp
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


class deepcoin:
    """
        docs: https://www.deepcoin.com/en/docs#deepcoin-market-tickers
    """
    def __init__(self):
        self.id = 'deepcoin'
        self.base_url = "https://api.deepcoin.com/deepcoin/"
        self.markets = {}  # not really needed, just a stub

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'market/tickers?instType=SPOT')
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
        tickers = data.get("data", [])
        for row in tickers:
            symbol = self._convert_symbol_to_ccxt(row.get('instId'))
            last = float(row.get('last', 0))
            currency_volume = last * float(row.get('vol24h', 0))
            # contact_volume = float(row.get('volCcy24h', 0))
            normalized_data[symbol] = {
                "last": last,
                "baseVolume": 0,
                "quoteVolume": currency_volume
            }

        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass
