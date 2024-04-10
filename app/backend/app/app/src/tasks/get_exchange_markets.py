import asyncio
import sys

from loguru import logger as lg
from src.deps.markets import Market
from src.lib.quotes import active_exchanges
from src.lib.utils import repeat_forever
import traceback



async def main():
    exchanges = active_exchanges
    # exchanges = ['bingx']
    await asyncio.gather(*[get_price_and_volume(ex=ex) for ex in exchanges])


@repeat_forever
async def get_price_and_volume(ex: str):
    """
        Get last price and volume for exchange tickers and store them to db
    """
    try:
        normalized_tickers = []
        async with Market(exchange_name=ex) as market:
            symbols = market.get_all_market_symbols()
            tickers = await market.fetch_all_tickers(symbols=symbols, target='vol')
            for symbol, prop in tickers.items():
                ticker = market.converter.get_normalized_ticker(symbol, prop)
                if ticker:
                    normalized_tickers.append(ticker)
            lg.info(f"{market.exchange_name} normalize {len(normalized_tickers)} tickers")
            await market.save_tickers(normalized_tickers)
    except Exception as e:
        err_msg = str(e)
        if "_abort" in err_msg:
            lg.warning(e)  # Library specific error when fails releasing resources
        else:
            lg.error(e.with_traceback(traceback.print_exc(100, sys.stdout)))


if __name__ == "__main__":
    asyncio.run(main())