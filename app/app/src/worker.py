import asyncio
from src.celery_app import app
from src.tasks.refresh import cache_refresh

@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(300.0, refresh_5m_cache.s(), name='Update 5min charts cache')
    sender.add_periodic_task(3600.0, refresh_1h_cache.s(), name='Update 1hour charts cache')
    sender.add_periodic_task(86400.0, refresh_1d_cache.s(), name='Update 1day charts cache')


@app.task
def refresh_5m_cache():
    asyncio.run(cache_refresh("5m"))

@app.task
def refresh_1h_cache():
    asyncio.run(cache_refresh("1h"))

@app.task
def refresh_1d_cache():
    asyncio.run(cache_refresh("1d"))