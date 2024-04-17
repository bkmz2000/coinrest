import asyncio
import sys
import traceback

import ccxt

import src.exchanges as my_exchanges
from src.db.connection import AsyncSessionFactory
from loguru import logger as lg
from src.deps.markets import Market
from src.lib.utils import NotActiveExchange, repeat_forever, CreateExchange
from src.db.cruds.crud_exchange import ExchangeCRUD
from src.strapi_sync.strapi import create_strapi_exchange
from src.lib.quotes import active_ccxt_exchanges
from src.exchanges import custom_exchanges


async def main():
    exchanges = await get_exchanges()
    # exchanges = ['coinspot', 'binance']
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
    except NotActiveExchange as nae:
        lg.warning(nae)
    except Exception as e:
        err_msg = str(e)
        if "_abort" in err_msg:
            lg.warning(e)  # Library specific error when fails releasing resources
        else:
            lg.error(e.with_traceback(traceback.print_exc(100, sys.stdout)))


async def get_exchanges() -> list[str]:
    """
        Import all implemented exchanges and sync them with local_db and strapi
    """
    all_exchanges = active_ccxt_exchanges + custom_exchanges
    crud = ExchangeCRUD()
    async with AsyncSessionFactory() as session:
        try:
            exchanges = await crud.get_all_exchanges(session=session)
            new_exchanges = list(set(all_exchanges) - set(exchanges))
            if new_exchanges:
                for exchange in new_exchanges:
                    # check ccxt exchanges
                    try:
                        ccxt_exchange = getattr(ccxt, exchange)()
                        ex_props = CreateExchange(
                            ccxt_name=ccxt_exchange.id,
                            full_name="",
                            cg_identifier=""
                        )
                        await crud.create(session=session, exchange=ex_props)  # store new exchange to db
                    except AttributeError:
                        exchange_obj = getattr(my_exchanges, exchange)()
                        ex_props = CreateExchange(
                            ccxt_name=exchange_obj.id,
                            full_name=exchange_obj.full_name,
                            cg_identifier=exchange_obj.cg_id
                        )
                        await crud.create(session=session, exchange=ex_props)  # store new exchange to db
                        await create_strapi_exchange(ex_props)  # store new exchange to strapi db
        except Exception as e:
            lg.error(e)
    return all_exchanges



if __name__ == "__main__":
    asyncio.run(main())