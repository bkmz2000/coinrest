from src.exchanges.base import BaseExchange


class bitstorage(BaseExchange):
    def __init__(self):
        self.id = "bitstorage"
        self.cg_id = "bitstorage"
        self.full_name = "Bitstorage"
        self.base_url = "https://api.bitstorage.finance"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        for k, v in self.markets.items():
            data = await self.fetch_data(self.base_url + f"/v1/public/ticker?pair={v}")
            result.update(self.normalize_data(data, k))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/v1/public/symbols")
        symbols = data["data"]
        for symbol in symbols:
            base = symbol["base"]
            quote = symbol["quote"]
            if base and quote:
                self.markets[base + "/" + quote] = base + quote

    def normalize_data(self, data: list, pair: str) -> dict[str, dict]:
        normalized_data = {}
        result = data["data"]
        symbol = self._convert_symbol_to_ccxt(pair)
        normalized_data[symbol] = {
            "last": float(result.get("last", 0)),
            "baseVolume": float(result.get("volume_24H", 0)),
            "quoteVolume": float(0),
        }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> dict:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
