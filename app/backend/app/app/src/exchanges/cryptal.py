from src.exchanges.base import BaseExchange


class cryptal(BaseExchange):
    def __init__(self):
        self.id = "cryptal"
        self.cg_id = "cryptal"
        self.full_name = "Cryptal"
        self.base_url = "https://exchange.cryptal.com/exchange"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        data = await self.fetch_data(self.base_url + "/api/v1/public/ticker")
        result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/api/v1/public/ticker")
        symbols = data
        for symbol in symbols:
            self.markets[symbol["pair"].replace("-", "/")] = symbol["pair"].replace(
                "-", ""
            )

    def normalize_data(self, data: list) -> dict[str, dict]:
        normalized_data = {}
        for result in data:
            symbol = self._convert_symbol_to_ccxt(result["pair"].replace("-", "/"))
            normalized_data[symbol] = {
                "last": float(result["lastTradePrice"]),
                "baseVolume": float(result["baseVolume"]),
                "quoteVolume": float(result["quoteVolume"]),
            }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
