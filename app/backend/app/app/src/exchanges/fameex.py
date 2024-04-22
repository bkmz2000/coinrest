from src.exchanges.base import BaseExchange


class fameex(BaseExchange):
    def __init__(self):
        self.id = "fameex"
        self.cg_id = "fameex"
        self.full_name = "Fameex"
        self.base_url = "https://api.fameex.com"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        data = await self.fetch_data(self.base_url + "/api/v2/ticker/price")
        result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/api/v2/ticker/price")
        symbols = data
        for symbol in symbols.keys():
            if symbol:
                self.markets[symbol.replace("-", "/")] = symbol.replace("-", "")

    def normalize_data(self, data: list) -> dict[str, dict]:
        normalized_data = {}
        for k, v in data.items():
            symbol = self._convert_symbol_to_ccxt(k)
            normalized_data[symbol.replace("-", "/")] = {
                "last": float(v.get("last_price", 0)),
                "baseVolume": float(v.get("base_volume", 0)),
                "quoteVolume": float(v.get("quote_volume", 0)),
            }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
