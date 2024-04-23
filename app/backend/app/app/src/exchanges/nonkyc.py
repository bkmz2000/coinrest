from src.exchanges.base import BaseExchange


class nonkyc_io(BaseExchange):
    def __init__(self):
        self.id = "nonkyc_io"
        self.cg_id = "nonkyc_io"
        self.full_name = "Nonkyc.io"
        self.base_url = "https://nonkyc.io"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        data = await self.fetch_data(self.base_url + "/api/v2/tickers")
        result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/api/v2/tickers")
        symbols = data
        for symbol in symbols:
            base = symbol["base_currency"]
            quote = symbol["target_currency"]
            if base and quote:
                self.markets[base + "/" + quote] = base + quote

    def normalize_data(self, data: list) -> dict[str, dict]:
        normalized_data = {}
        for result in data:
            symbol = self._convert_symbol_to_ccxt(result.get("ticker_id"))
            normalized_data[symbol] = {
                "last": float(result.get("last_price", 0)),
                "baseVolume": float(result.get("base_volume", 0)),
                "quoteVolume": float(result.get("target_volume", 0)),
            }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
