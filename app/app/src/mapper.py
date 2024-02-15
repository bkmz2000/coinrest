import asyncio
from contextlib import suppress

import ccxt.pro
from asyncio import run
from loguru import logger as lg
from ccxt.async_support.base.exchange import BaseExchange
from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from src.lib.client import fetch_data_from_hodler
from src.lib.utils import GeckoMarkets, BaseMapper
from src.db.crud import set_mapper_data, get_mapper_data, get_exchange_cg_ids



async def get_mapper(exchanges: list[BaseExchange], session: AsyncSession) -> dict[str, list[GeckoMarkets]]:
    lg.info(f"Loading mapper from database")
    data = await get_mapper_data(session=session)
    mapper = defaultdict(list)
    for market in data:
        for exchange in exchanges:
            if exchange.id == market.exchange:
                mapper[market.cg_id].append(GeckoMarkets(symbol=market.symbol, exchange=exchange))
                break
    # for k, v in mapper.items():
    #     lg.info(f"{k}: mapped {len(v)} exchanges")
    return mapper


async def get_cg_ids(session: AsyncSession, exchange_id: str):
    ids = {}
    cg_ids = await get_exchange_cg_ids(session=session, exchange_id=exchange_id)
    for market in cg_ids:
        base = market['symbol'].split("/")[0]
        ids[base] = market['cg_id']
    lg.debug(f"{exchange_id} coingecko_ids: {ids}")
    return ids

async def _fetch_all_tickers(ex: BaseExchange, symbols: set):
    result = {}
    returned = 0
    for i in range(3):
        # Fetch tickers and find all .../USDT(symbol) in it
        try:
            tickers = await ex.fetch_tickers()
            lg.debug(len(tickers))
            for symbol, prop in tickers.items():
                last_price = prop.get('last')
                # lg.info(f"{symbol}: {last_price} {prop}")
                if symbol in symbols:
                    symbols.remove(symbol)  # Remove if symbol present in tickers...
                if last_price is None and symbol.endswith("/USDT"):  # ...But return if it's price is None, so we'll request it below
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
            lg.debug(f"{ex.id} fetched ticker: {ticker}")
            result[symbol] = ticker
        except Exception as e:
            if "delisted" in str(e):
                continue
            lg.error(f"{symbol}: {e}")
    return result

def _get_usdt_symbols(ex: BaseExchange) -> set:
    """
        Get all symbols that can be calculated in USDT, and can be matched to coingecko_id
    """
    symbols = set()
    for symbol, prop in ex.markets.items():
        if ":" in symbol or "/" not in symbol:  # ':' only in derivative symbol, skip it
            continue
        if prop["quote"] == "USDT":
            symbols.add(symbol)
    return symbols


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


async def update_mapper(exchanges: list[BaseExchange], session: AsyncSession) -> dict[str, list[GeckoMarkets]]:
    lg.info("Updating mapper")
    mapper = defaultdict(list)

    coins = await fetch_data_from_hodler()

    total_counter = 0
    success_counter = 0

    pairs = set()  # Уникальные торговые пары
    ex_pairs = dict()  # Торговые пары для конкретной биржи

    for exchange in exchanges:
        tickers = await _find_exchange_USDT_tickers(exchange, pairs, ex_pairs)
        lg.info(tickers)
        try:
            symbols = _get_usdt_symbols(exchange)
            result = await _fetch_all_tickers(ex=exchange, symbols=symbols)
            prices = _get_last_prices(result)
            lg.info(prices)

            for usdt_ticker in tickers:
                ticker = result.get(usdt_ticker, {})
                if not ticker or not ticker.get("last"):
                    continue
                data = {
                    "symbol": exchange.markets[ticker["symbol"]]["base"],
                    "value": ticker.get("last")
                }
                total_counter += 1
                cg_id = match_id(coins, data)
                if cg_id:
                    mapper = BaseMapper(cg_id=cg_id, exchange=exchange.id, symbol=ticker["symbol"])
                    await set_mapper_data(session=session, mapper=mapper)
                    # mapper[cg_id].append(GeckoMarkets(symbol=ticker["symbol"], exchange=exchange))
                    success_counter += 1
                lg.info(f"{total_counter}/{success_counter}, {data}, {cg_id}")
        except Exception as e:
            lg.error(f"{exchange.id} - {e}")

    lg.info(f"Number of currencies: {len(pairs)}")
    # lg.info(f"Uniques: {pairs}")
    return mapper


async def _find_exchange_USDT_tickers(ex, pairs, ex_pairs) -> list[str]:
    """
        Для биржи находим все торговые пары {ticker}/USDT
    """
    ex_pairs[ex.id] = []
    for market, prop in ex.markets.items():
        if ":" in market or "/" not in market:  # ':' only in derivative symbol, so skip it
            continue
        if prop["quote"] == "USDT":
            pairs.add(market)
            ex_pairs[ex.id].append(market)
    ex_pairs[ex.id] = list(set(ex_pairs[ex.id]))
    lg.info(f"{ex.id}: {len(ex_pairs[ex.id])}")
    return ex_pairs[ex.id]


def match_id(coins: list, item: dict):
    exchange_symbol = item.get("symbol")

    for coin in coins:
        if coin["symbol"] == exchange_symbol:
            if 0.95 <= coin["quote"]["USD"]["price"] / item["value"] <= 1.05:
                return coin["cgid"]

async def main():
    from src.deps.markets import AllMarketsLoader
    from src.db.connection import AsyncSessionFactory
    # exs = AllMarketsLoader(ccxt.exchanges)
    # exs = AllMarketsLoader(['binance', 'mexc'])
    # exs = AllMarketsLoader(exchange_names=['bybit'])
    exs = AllMarketsLoader()
    await exs.start()
    ex_markets = exs.get_target_markets(target="volume")
    async with AsyncSessionFactory() as session:
        mapper = await update_mapper(ex_markets, session=session)
        print(mapper)
    await exs.close()



if __name__ == '__main__':
    run(main())
