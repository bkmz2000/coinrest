from src.exchanges.base import BaseExchange


class gmo_japan(BaseExchange):
    """
        docs: https://github.com/catex/catex_exchange_api/wiki/Acquire-all-trading-pairs-volume-and-price-by-list
    """
    def __init__(self):
        self.id = 'gmo_japan'
        self.cg_id = "gmo_japan"
        self.full_name = "GMO Japan"
        self.base_url = "https://api.coin.z.com/public/"
        self.markets = {}


    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'v1/ticker')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str) -> str | None:
        if isinstance(symbols, str):
            if symbols.endswith("_JPY"):
                return None
            symbols += '/JPY'
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        tickers = data.get('data', {})
        for ticker in tickers:
            symbol = self._convert_symbol_to_ccxt(ticker.get('symbol'))
            if symbol:
                normalized_data[symbol] = {
                    "last": float(ticker.get("last", 0)),
                    "baseVolume": float(ticker.get("volume", 0)),
                    "quoteVolume": 0,
                }
        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
