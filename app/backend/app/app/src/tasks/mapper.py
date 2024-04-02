from asyncio import run
from loguru import logger as lg

from src.db.connection import AsyncSessionFactory
from src.lib.client import fetch_data_from_hodler
from src.lib.utils import TickerToMatch, TickerMatched
from src.db import crud
from src.db.cruds import crud_exchange


async def update_mapper():
    """
        Updates tickers/coingecko ids for all exchanges for all tickers
    :return:
    """
    lg.info("Updating mapper")
    coins = await fetch_data_from_hodler()
    # coins = []
    matched = []
    ex = crud_exchange.ExchangeCRUD()
    async with AsyncSessionFactory() as session:
        db_tickers = await crud.get_db_tickers(session=session)
        for ticker in db_tickers:
            lg.debug(ticker)
            matched_ticker = match(coins, ticker)
            if matched_ticker:
                await ex.save_mappings(session=session,
                                       exchange_id=matched_ticker.exchange_id,
                                       mapped={matched_ticker.symbol: matched_ticker.base_cg})
        lg.info(f"Matched tickers: {len(matched)}/{len(db_tickers)}")

def match(coins: list, ticker: TickerToMatch) -> TickerMatched | None:
    """
        Match symbol with current price to coingecko_id
    :param coins: coingecko ids with actual prices
    :param ticker: ticker from db, we try to match
    :return: Matched ticker to coingecko id or None
    """
    for coin in coins:
        if coin["symbol"] == ticker.base:
            if 0.85 <= coin["quote"]["USD"]["price"] / ticker.price_usd <= 1.15:
                return TickerMatched(exchange_id=ticker.exchange_id, base_cg=coin["cgid"], symbol=ticker.base)


async def main():
    await update_mapper()



if __name__ == '__main__':
    run(main())
