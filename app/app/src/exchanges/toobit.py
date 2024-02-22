import aiohttp
from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


class toobit:
    """
        docs: https://toobit-docs.github.io/apidocs/spot/v1/en/#24hr-ticker-price-change-statistics
    """
    def __init__(self):
        self.id = 'toobit'
        self.base_url = "https://api.toobit.com/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()

        result = {}
        for symbol in self.markets.values():
            data = await self.fetch_data(self.base_url + 'quote/v1/ticker/24hr?symbol=' + symbol)
            # lg.debug(f"Fetched {data}")
            result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "api/v1/exchangeInfo")
        symbols = data.get("symbols", [])
        for symbol in symbols:
            base = symbol["baseAsset"]
            quote = symbol["quoteAsset"]
            if base and quote:
                self.markets[base + "/" + quote] = base+quote

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
        result = data[0]
        symbol = self._convert_symbol_to_ccxt(result.get("s"))
        normalized_data[symbol] = {
            "last": float(result.get("c", 0)),
            "baseVolume": float(result.get("v", 0)),
            "quoteVolume": float(result.get("qv", 0))
        }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            if symbols.endswith("USDT"):
                symbols = symbols.replace("USDT", "/USDT")
            return symbols
        raise TypeError(f"{symbols} invalid type")

    async def close(self):
        pass