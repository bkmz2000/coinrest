from src.exchanges.base import BaseExchange


class onetrading(BaseExchange):
    def __init__(self):
        self.id = "bitpanda"
        self.cg_id = "bitpanda"
        self.full_name = "One Trading"
        self.base_url = "https://api.onetrading.com"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        data = await self.fetch_data(self.base_url + "/fast/v1/market-ticker")
        result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/fast/v1/market-ticker")
        symbols = data
        for symbol in symbols:
            code = symbol["instrument_code"]
            self.markets[code.replace("_", "/")] = code.replace("_", "/")

    def normalize_data(self, data: list) -> dict[str, dict]:
        normalized_data = {}
        for result in data:
            symbol = self._convert_symbol_to_ccxt(result["instrument_code"])
            normalized_data[symbol] = {
                "last": float(result.get("last_price", 0)),
                "baseVolume": float(result.get("base_volume", 0)),
                "quoteVolume": float(result.get("quote_volume", 0)),
            }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
