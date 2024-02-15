import asyncio
import datetime
import time
from collections import defaultdict
from loguru import logger as lg

from ccxt.async_support.base.exchange import BaseExchange
from src.db.crud import save_last_volumes
from src.deps.markets import AllMarketsLoader
from src.mapper import get_cg_ids
from src.lib import utils
from src.db.connection import AsyncSessionFactory
from src.lib.utils import sleeping


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
    async with AsyncSessionFactory() as session:
        ids = await get_cg_ids(session=session, exchange_id=ex.id)
    symbols = _get_usdt_symbols(ex, ids)
    tickers = await _fetch_all_tickers(ex=ex, symbols=symbols, ids=ids)
    prices = _get_last_prices(tickers)
    # for k, v in tickers.items():
    #     lg.info(f"{k}: {v}")

    # Перебираем все монеты, считаем volume по курсу определенному выше, или из quoteVolume
    for symbol, prop in tickers.items():
        # lg.info(f"{symbol}: {prop}")
        if ":" in symbol or "/" not in symbol:  # ':' or no '/' - means derivative, so skip it.
            continue

        # lg.info(f"{ex.id}-{symbol}")
        base = symbol.split("/")[0]
        cg_id = ids.get(base)
        rate = prices.get(base)
        volume = _get_volume(ex=ex, prop=prop, rate=rate)

        if cg_id and volume is not None:
            coins[cg_id].volume += volume
            coins[cg_id].price = rate
            coins[cg_id].exchange = ex.id
            # lg.info(f"{ex.id}-{symbol}: {volume:_}")

    async with AsyncSessionFactory() as session:
        await save_last_volumes(session=session, coins=coins)


async def _fetch_all_tickers(ex: BaseExchange, symbols: set, ids: dict):
    """
        Запрашиваем все маркеты доступные на бирже.
        Если какие-то маркеты не придут из fetchTickers(),
        дополнительно зпарашиваем fetchTicker()
    """
    result = {}
    returned = 0
    for i in range(3):
        # Fetch tickers and find all .../USDT(symbol) in it
        try:
            tickers = await ex.fetch_tickers()
            for symbol, prop in tickers.items():
                # lg.info(f"{symbol}: {prop}")
                volume = prop.get('baseVolume')
                if symbol in symbols:
                    symbols.remove(symbol)  # Remove if symbol present in tickers...
                if volume is None:  # ...But return if it's volume is None, so we'll request it below
                    if ":" in symbol or "/" not in symbol:  # ':' or no '/' - means derivative, so skip it.
                        continue
                    base = symbol.split("/")[0]
                    if base in ids:  # ...And return only ones we can match to coingecko_id
                        returned += 1
                        symbols.add(symbol)
            result.update(tickers)

            break
        except Exception as e:
            lg.error(e)
            await asyncio.sleep(0.5)
    lg.debug(f"{ex.id} returned to fetch: {returned}")
    # If some .../USDT(symbol) not in tickers, fetch it
    lg.debug(f"{ex.id} has {len(symbols)} not in tickers")
    if not symbols:
        return result

    for symbol in symbols:
        await asyncio.sleep(ex.fetch_timeout)
        try:
            ticker = await ex.fetch_ticker(symbol)
            lg.debug(f"{ex.id} fetched ticker: {ticker.get('symbol')}")
            result[symbol] = ticker
        except Exception as e:
            if "delisted" in str(e):
                continue
            lg.error(f"{symbol}: {e}")
    return result


def _get_last_prices(tickers: dict) -> dict[str, float]:
    """
        Get price for base value in USD (tether) (in BTC/USDT btc-base, usdt-quote)
    :param tickers:
    :return: dict with BASE price amount (BTC: 4213, ETH: 123)
    """
    prices = {}
    for symbol, prop in tickers.items():
        if symbol.endswith("/USDT"):
            base = symbol.split("/USDT")[0]
            if prop['last']:
                prices[base] = prop['last']
    return prices


def _get_usdt_symbols(ex: BaseExchange, cg_ids: dict) -> set:
    """
        Get all symbols that can be calculated in USDT, and can be matched to coingecko_id
    """
    bases = set()
    for symbol, prop in ex.markets.items():
        if ":" in symbol or "/" not in symbol:  # ':' or no '/' - means derivative, so skip it.
            continue
        if prop["quote"] == "USDT":
            bases.add(prop['base'])
    lg.debug(f"{ex.id} bases: {bases}")

    cg_miss = _show_diff(ex, bases, cg_ids)

    symbols = set()
    for symbol, prop in ex.markets.items():
        if ":" in symbol or "/" not in symbol:  # ':' or no '/' - means derivative, so skip it.
            continue
        if prop["base"] in cg_miss:  # do not request ticker, we cannot map
            continue

        if prop["base"] in bases:
            symbols.add(symbol)
    lg.debug(f"{ex.id} symbols: {symbols}")
    return symbols


def _get_volume(ex: BaseExchange, prop: dict, rate: float) -> float | None:
    """
    :param prop: Ticker properties
    :param rate: Base currency rate
    :return: volume in USD (USDT, USDC)
    """
    volume = prop.get('baseVolume')
    if volume is not None and rate is not None:
        return volume * rate

    quote = prop.get('symbol', '').split("/")[1]
    volume = prop.get('quoteVolume')
    if volume is not None and quote in ("USD", "USDT", "USDC"):
        return volume
    else:
        lg.warning(f"{ex.id} cannot parse volume for: {prop.get('symbol')}")
        return None


def _show_diff(ex: BaseExchange, bases: set, cg_ids: dict):
    """
        Check how many currencies we can't map to coingecko id
    :param ex: Exchange instance
    :param bases: base currency
    :param cg_ids: list of mapped coingecko ids
    :return: None
    """
    miss = []
    if len(bases) != len(cg_ids):
        for base in bases:
            if base not in cg_ids:
                miss.append(base)
    if miss:
        lg.warning(f"{ex.id} coingecko map miss for {len(miss)}: {miss}")
    return miss


if __name__ == "__main__":
    asyncio.run(main())