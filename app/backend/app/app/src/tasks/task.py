import os
import asyncio

import redis.asyncio as redis
from src.db.cache import set_to_cache
from src.celery_app import app


@app.task(ignore_result=True)
def set_cache_task(**kwargs):
    asyncio.run(set_cache(**kwargs))


async def set_cache(*args, **kwargs):
    r = redis.Redis(host=os.getenv("REDIS_HOST"), port=int(os.environ.get("REDIS_PORT")), decode_responses=True)
    cg_id = kwargs.get('cg_id')
    currency = kwargs.get('currency')
    timeframe = kwargs.get('timeframe')
    value = kwargs.get('value')
    await set_to_cache(r=r, cg_id=cg_id, currency=currency, timeframe=timeframe, value=value)
    await r.aclose()
