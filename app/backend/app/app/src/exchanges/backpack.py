from src.exchanges.base import BaseExchange


class backpack_exchange(BaseExchange):
    def __init__(self):
        self.id = "backpack_exchange"
        self.cg_id = "backpack_exchange"
        self.full_name = "Backpack Exchange"
        self.base_url = "https://api.backpack.exchange"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        data = await self.fetch_data(self.base_url + "/api/v1/tickers")
        result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/api/v1/tickers")
        symbols = data
        for symbol in symbols:
            self.markets[symbol["symbol"].replace("_", "/")] = symbol["symbol"].replace(
                "_", ""
            )

    def normalize_data(self, data: list) -> dict[str, dict]:
        normalized_data = {}
        for result in data:
            symbol = self._convert_symbol_to_ccxt(result["symbol"].replace("_", "/"))
            normalized_data[symbol] = {
                "last": float(result["lastPrice"]),
                "baseVolume": float(result["volume"]),
                "quoteVolume": float(result["quoteVolume"]),
            }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
