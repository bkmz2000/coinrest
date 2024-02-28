import asyncio
from loguru import logger as lg
from src.deps.markets import AllMarketsLoader
from src.deps.markets import Market
from src.lib.quotes import active_exchanges
from src.lib.utils import sleeping

quotes = []


async def main():
    exchanges = active_exchanges
    await asyncio.gather(*[get_price_and_volume(ex=ex) for ex in exchanges])


# @sleeping
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
                    # lg.info(ticker)
                    normalized_tickers.append(ticker)
            lg.info(f"{market.exchange_name} normalize {len(normalized_tickers)} tickers")
            await market.save_tickers(normalized_tickers)
    except Exception as e:
        lg.error(e)


async def mmain():
    exchanges = active_exchanges
    # exchanges = ['orangex']
    await asyncio.gather(*[get_price_and_volume(ex=ex) for ex in exchanges])


if __name__ == "__main__":
    asyncio.run(mmain())