from src.exchanges.base import BaseExchange


class xeggex(BaseExchange):
    def __init__(self):
        self.id = "xeggex"
        self.cg_id = "xeggex"
        self.full_name = "XeggeX"
        self.base_url = "https://api.xeggex.com/api/v2/"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        data = await self.fetch_data(self.base_url + "/market/getlist")
        return self.normalize_data(data)

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/market/getlist")
        symbols = data
        for symbol in symbols:
            symbol_ = symbol["symbol"]
            if symbol_:
                self.markets[symbol_] = symbol_

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def normalize_data(self, data: dict) -> dict[str, dict]:
        normalized_data = {}
        for result in data:
            symbol = self._convert_symbol_to_ccxt(result.get("symbol"))
            normalized_data[symbol] = {
                "last": float(result.get("lastPrice", 0)),
                "baseVolume": float(result.get("volume", 0)),
                "quoteVolume": float(0),
            }
        return normalized_data
