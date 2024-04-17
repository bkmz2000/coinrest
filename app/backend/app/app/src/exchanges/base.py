"""
    Description: For an exchange, get all trading pairs, their latest prices and trading volume for 24 hours
    Task:
        Create a class inherited from the BaseExchange class.
        Write the implementation of the methods and fill in the required fields (marked as "todo")
    Note:
        Feel free to add another internal methods.
        It is important that the example from the main function runs without errors
    The flow looks like this:
        1. Request data from the exchange
        2. We bring the ticker to the general format
        3. We extract from the ticker properties the last price,
            the 24-hour trading volume of the base currency
            and the 24-hour trading volume of the quoted currency.
            (at least one of the volumes is required)
        4. Return the structure in the format:
            {
                "BTC/USDT": TickerInfo(last=57000, baseVolume=11328, quoteVolume=3456789),
                "ETH/BTC": TickerInfo(last=4026, baseVolume=4567, quoteVolume=0)
            }
"""
import asyncio
import aiohttp

class BaseExchange:
    async def fetch_data(self, url: str):
        """
        :param url: URL to fetch the data from exchange
        :return: raw data
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp and resp.status == 200:
                    data = await resp.json()
                else:
                    raise Exception(resp)
        return data

    async def fetch_tickers(self) -> dict[str, dict]:
        """
        Method fetch data from exchange and return all tickers in normalized format
        :return:
        """
        raise NotImplementedError

    def normalize_data(self, data: dict) -> dict[str, dict]:
        """
        :param data: raw data received from the exchange
        :return: normalized data in a common format
        """
        raise NotImplementedError

    def _convert_symbol_to_ccxt(self, symbols: str) -> str:
        """
        Trading pairs from the exchange can come in various formats like: btc_usdt, BTCUSDT, etc.
        Here we convert them to a value like: BTC/USDT.
        The format is as follows: separator "/" and all characters in uppercase

        :param symbols: Trading pair ex.: BTC_USDT
        :return: BTC/USDT
        """
        raise NotImplementedError

    async def load_markets(self):
        """
        Sometimes the exchange does not have a route to receive all the tickers at once.
        In this case, you first need to get a list of all trading pairs and save them to self.markets.(Ex.2)
        And then get all these tickers one at a time.
        Allow for delays between requests so as not to exceed the limits
        (you can find the limits in the documentation for the exchange API)
        """
    async def close(self):
        pass