import asyncio
from typing import Literal

from ccxt.async_support.base.exchange import BaseExchange
from loguru import logger as lg


important_field = {
    "map": 'last',
    "vol": 'baseVolume'
}

async def fetch_all_tickers(ex: BaseExchange, symbols: set, target: Literal['map', 'vol'] = 'map') -> dict:
    """
        Fetch tickers with 3 steps:
             1. Try to fetch ALL tickers with 1 request
             2*. If not all tickers were returned, or some of them with null volume,
             try to fetch tickers as batch
             3*. If some tickers still not returned, try to fetch them one by one
        :param target: Purpose of func executing. For mapping(map) important field in ticker -> 'last',
        for volume counting(vol) -> 'volume'
        :param ex: Exchange instance
        :param symbols: unique trading pairs without derivatives
        :return: tickers
        """
    result = {}
    returned = 0
    target = important_field.get(target)
    for i in range(3):
        # Fetch all tickers
        try:
            tickers = await ex.fetch_tickers()
            result.update(tickers)

            lg.debug(len(tickers))
            for symbol, prop in tickers.items():
                field = prop.get(target)
                if symbol in symbols:
                    symbols.remove(symbol)  # Remove if symbol present in tickers...
                if field is None:  # ...But return if field is None, so we'll request it below
                    if ":" in symbol or "/" not in symbol:
                        continue
                    returned += 1
                    symbols.add(symbol)
            break
        except Exception as e:
            lg.error(e)
            await asyncio.sleep(0.5)

    if not symbols:
        return result

    lg.debug(f"{ex.id} has {len(symbols)} not in tickers, returned: {returned}")
    # If some symbol not in tickers, try to fetch them as a batch
    l_symbols = list(symbols)
    batch = 50
    for i in range(0, len(symbols), batch):
        await asyncio.sleep(ex.fetch_timeout)
        try:
            lg.debug(f"{ex.id}: {l_symbols[i:i + batch][:10]}, {i}, {i + batch}")
            tickers = await ex.fetch_tickers(symbols=l_symbols[i:i + batch])
            result.update(tickers)

            for symbol, prop in tickers.items():
                field = prop.get(target)
                if symbol in symbols:
                    symbols.remove(symbol)  # Remove if symbol present in tickers...
                if field is None:  # ...But return if field is None, so we'll request it below
                    if ":" in symbol or "/" not in symbol:
                        continue
                    returned += 1
                    symbols.add(symbol)
        except Exception as e:
            lg.error(e)
    if not symbols:
        return result

    lg.debug(f"{ex.id} has {len(symbols)} to fetch by one")
    # If some symbol not in tickers, try to fetch them one by one
    for symbol in symbols:
        if ":" in symbol or "/" not in symbol:
            continue
        await asyncio.sleep(ex.fetch_timeout)
        try:
            ticker = await ex.fetch_ticker(symbol)
            lg.debug(f"{ex.id} fetched ticker: {ticker}")
            result[symbol] = ticker
        except Exception as e:
            # if "delisted" in str(e):
            #     continue
            lg.error(f"{symbol}: {e}")
    return result


def get_all_market_symbols(ex: BaseExchange) -> set:
    """
        Get all symbols without derivatives
    """
    symbols = set()
    for symbol, prop in ex.markets.items():
        if ":" in symbol or "/" not in symbol:  # ':' and no '/' only in derivative symbol, skip it
            continue
        symbols.add(symbol)
    return symbols
