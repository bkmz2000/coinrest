import asyncio
from src.celery_app import app
from src.tasks.total_markets import main as calculate_last_price
from src.tasks.new_mapper import main as update_mapper
from src.tasks.mapper import main as old_update_mapper
from src.tasks.rates import main as update_quote_currency
from src.tasks.last_price import main as last_tickers
from src.tasks.strapi_sync import main as strapi_sync


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    ...
    sender.add_periodic_task(300.0, update_quote_currency_task.s(), name="Update quote currency rates")
    sender.add_periodic_task(43200.0, update_mapper_task.s(), name="Update mapper for all exchanges")
    sender.add_periodic_task(300.0, calculate_last_price_task.s(), name='Calculate actual last prices and 24_volumes')
    sender.add_periodic_task(300.0, strapi_sync_task.s(), name="Sync strapi exchanges data with local db")


@app.task()
def last_tickers_task():
    asyncio.run(last_tickers())


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
