import asyncio
import os
from loguru import logger as lg
from celery import chain

from src.celery_app import app
from src.tasks.calculate_total_markets import main as calculate_last_price
from src.tasks.update_coingecko_mapper import main as update_mapper
from src.tasks.force_mapper import main as old_update_mapper
from src.tasks.update_rates import main as update_quote_currency
from src.tasks.get_exchange_markets import main as last_tickers
from src.tasks.strapi_sync import main as strapi_sync
from src.tasks.update_actual_coin_ids import main as update_coingecko_actual
from src.tasks.get_coingecko_markets import main as gecko_markets
from src.tasks.update_historical_ohlc import main as historical_ohlc
from src.tasks.update_historical_last import main as historical_last
from src.tasks.top_volume_tickers import main as top_volume_tickers
from src.tasks.market_depth import main as market_depth
from src.tasks.socket_last import main as socket_watch


IS_DEV = os.environ.get("IS_DEV", False)

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    ...
    sender.add_periodic_task(300.0, last_price_chain_task.s(), name="Last values calculation tasks chain")  # Calculate last_price then store it to hist db
    sender.add_periodic_task(300.0, update_quote_currency_task.s(), name="Update quote currency rates")
    # sender.add_periodic_task(300.0, calculate_last_price_task.s(), name='Calculate actual last prices and 24_volumes') in chain
    sender.add_periodic_task(300.0, strapi_sync_task.s(), name="Sync strapi exchanges data with local db")
    sender.add_periodic_task(250.0, soket_watching_task.s(), name="Socket watching task")

    # Historical tasks
    sender.add_periodic_task(1200.0, top_historical_task.s(), name="Update top historical data from exchanges ohlcv")
    # sender.add_periodic_task(9000.0, all_historical_task.s(), name="Update all historical data from exchanges ohlcv")
    # sender.add_periodic_task(300.0, historical_last_task.s(), name="Update historical table from last values, delete old data") in chain

    # Coingecko tasks
    sender.add_periodic_task(43200.0, update_mapper_task.s(), name="Update mapper for all exchanges")
    sender.add_periodic_task(300.0, update_coingecko_actual_task.s(), name="Update list of actual coingecko coins")
    if not IS_DEV:
        sender.add_periodic_task(300.0, gecko_markets_task.s(), name="Get market data from coingecko")
    # Market depth
    sender.add_periodic_task(1500.0, market_depth_chain_task.s(), name="Market depth calculation tasks chain")

@app.task(bind=True, default_retry_delay=30)
def last_tickers_task(self):
    try:
        asyncio.run(last_tickers())
    except Exception as e:
        lg.error(e)
        raise self.retry(exc=e, countdown=30)


@app.task(time_limit=290)
def calculate_last_price_task():
    asyncio.run(calculate_last_price())


@app.task
def update_mapper_task():
    asyncio.run(update_mapper())


@app.task
def old_update_mapper_task():
    asyncio.run(old_update_mapper())


@app.task(time_limit=290)
def update_quote_currency_task():
    asyncio.run(update_quote_currency())


@app.task(time_limit=290)
def strapi_sync_task():
    asyncio.run(strapi_sync())


@app.task(time_limit=60)
def update_coingecko_actual_task():
    asyncio.run(update_coingecko_actual())


@app.task(time_limit=290)
def gecko_markets_task():
    asyncio.run(gecko_markets())


@app.task(time_limit=900)
def top_historical_task(*args, **kwargs):
    return asyncio.run(historical_ohlc(**{"limit": 500}))


@app.task(time_limit=9000)
def all_historical_task(*args, **kwargs):
    return asyncio.run(historical_ohlc(**{"limit": None}))


@app.task(time_limit=120)
def historical_last_task(*args, **kwargs):
    asyncio.run(historical_last())


@app.task(time_limit=100)
def last_price_chain_task():
    chain(calculate_last_price_task.s(), historical_last_task.s())()


@app.task(time_limit=100)
def copy_top_volume_tickers_task(*args, **kwargs):
    asyncio.run(top_volume_tickers())


@app.task(time_limit=1500)
def calculate_market_depth_task(*args, **kwargs):
    asyncio.run(market_depth())


@app.task(time_limit=1500)
def market_depth_chain_task():
    chain(copy_top_volume_tickers_task.s(), calculate_market_depth_task.s())()


@app.task(time_limit=60)
def soket_watching_task():
    asyncio.run(socket_watch())
