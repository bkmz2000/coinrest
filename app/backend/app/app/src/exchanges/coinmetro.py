from src.exchanges.base import BaseExchange


class coinmetro(BaseExchange):
    """
        docs: https://documenter.getpostman.com/view/3653795/SVfWN6KS#6ecd1cd1-f162-45a3-8b3b-de690332a485
    """
    def __init__(self):
        self.id = 'coinmetro'
        self.cg_id = "coin_metro"
        self.full_name = "Coinmetro"
        self.base_url = "https://api.coinmetro.com/"
        self.markets = {}

    async def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, dict]:
        if symbols:
            return {}
        data = await self.fetch_data(self.base_url + 'exchange/prices')
        return self.normalize_data(data)

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        if isinstance(symbols, str):
            return self.markets.get(symbols)
        raise TypeError(f"{symbols} invalid type")

    def _convert_symbol_from_ccxt(self, symbol: str | list[str]) -> str:
        pass

    def normalize_data(self, data: dict) -> dict:
        normalized_data = {}
        last_prices = data.get("latestPrices", [])
        for price in last_prices:
            symbol = self._convert_symbol_to_ccxt(price.get("pair"))
            normalized_data[symbol] = {
                "last": float(price.get("price", 0))
            }
        volumes = data.get("24hInfo", [])
        for volume in volumes:
            symbol = self._convert_symbol_to_ccxt(volume.get("pair"))
            normalized_data[symbol].update({
                "baseVolume": volume.get("v", 0),
                "quoteVolume": 0,
            })
        return normalized_data

    async def load_markets(self):
        assets = await self.fetch_data(self.base_url + 'assets')
        assets = {asset.get("symbol") for asset in assets}

        markets = await self.fetch_data(self.base_url + 'markets')
        markets = [market.get("pair") for market in markets]
        for market in markets:
            for i in range(2, len(market), 1):
                base, quote = market[0: i], market[i:]
                if base in assets and quote in assets and len(base)+len(quote) == len(market):
                    self.markets[market] = base + "/" + quote
                    break

    async def close(self):
        pass  # stub, not really needed
