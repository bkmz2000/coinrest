import asyncio
from collections import defaultdict
from loguru import logger as lg
from src.deps.markets import AllMarketsLoader
from ccxt.async_support.base.exchange import BaseExchange
from src.db.crud import save_last_volumes
from src.deps.converter import Converter
from src.lib import utils
from src.tasks.methods import get_all_market_symbols, fetch_all_tickers
from src.db.connection import AsyncSessionFactory
from src.lib.utils import sleeping

quotes = []

async def main():
    # exs = AllMarketsLoader(exchange_names=["binance"])
    exs = AllMarketsLoader()
    await exs.start()
    exchanges = exs.get_target_markets(target="volume")

    await asyncio.gather(*[get_price_and_volume(ex=ex) for ex in exchanges])
    await exs.close()


@sleeping
async def get_price_and_volume(ex: BaseExchange):
    """
        Get last price and volume for exchange and store it to db
    """
    coins = defaultdict(utils.Coin)
    async with Converter(exchange=ex) as converter:
        symbols = get_all_market_symbols(ex)
        tickers = await fetch_all_tickers(ex=ex, symbols=symbols, target='vol')
        for symbol, prop in tickers.items():
        #     lg.debug(f"{symbol}: {prop}")
            converter.get_volumes(symbol, prop, coins)
        # for k, v in coins.items():
        #     lg.debug(f"{k}: {v}")
    async with AsyncSessionFactory() as session:
        await save_last_volumes(session=session, coins=coins)


async def mmain():
    # exs = AllMarketsLoader(exchange_names=["coinbasepro"])
    exs = AllMarketsLoader()
    await exs.start()
    exchanges = exs.get_target_markets(target="volume")
    await asyncio.gather(*[get_price_and_volume(ex=ex) for ex in exchanges])
    await exs.close()


if __name__ == "__main__":
    asyncio.run(mmain())