from src.exchanges.base import BaseExchange


class qmall(BaseExchange):
    """
        docs: https://gitlab.com/qMall-ex/api/-/wikis/Trading#public-methods
    """
    def __init__(self):
        self.id = 'qmall'
        self.cg_id = "qmall"
        self.full_name = "QMall"
        self.base_url = "https://api.qmall.io/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'api/v1/public/tickers')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            symbols = symbols.replace("_", "/")
            return symbols
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        tickers = data.get('result', {})
        for symbol, prop in tickers.items():
            ticker = prop['ticker']
            symbol = self._convert_symbol_to_ccxt(symbol)
            normalized_data[symbol] = {
                "last": float(ticker.get("last", 0)),
                "baseVolume": float(ticker.get("vol", 0)),
                "quoteVolume": float(ticker.get("deal", 0)),
            }
        return normalized_data

    async def load_markets(self):
        pass  # stub, not really needed

    async def close(self):
        pass  # stub, not really needed
