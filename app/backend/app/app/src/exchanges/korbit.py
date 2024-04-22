from src.exchanges.base import BaseExchange


class korbit(BaseExchange):
    def __init__(self):
        self.id = "korbit"
        self.cg_id = "korbit"
        self.full_name = "Korbit"
        self.base_url = "https://api.korbit.co.kr"
        self.markets = {}

    async def fetch_tickers(self) -> dict[str, dict]:
        if not self.markets:
            await self.load_markets()
        result = {}
        data = await self.fetch_data(self.base_url + "/v1/ticker/detailed/all")
        result.update(self.normalize_data(data))
        return result

    async def load_markets(self):
        data = await self.fetch_data(self.base_url + "/v1/ticker/detailed/all")
        symbols = data
        for symbol in symbols.keys():
            if symbol:
                self.markets[symbol.replace("_", "/").upper()] = symbol.replace(
                    "_", ""
                ).upper()

    def normalize_data(self, data: list) -> dict[str, dict]:
        normalized_data = {}
        for k, v in data.items():
            symbol = self._convert_symbol_to_ccxt(k)
            normalized_data[symbol.replace("-", "/").upper()] = {
                "last": float(v.get("last", 0)),
                "baseVolume": float(v.get("volume", 0)),
                "quoteVolume": float(0),
            }
        return normalized_data

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")
