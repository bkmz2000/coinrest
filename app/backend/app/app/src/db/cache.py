import asyncio
import json
import time

from redis.asyncio import Redis
from loguru import logger as lg

expirations = {
    "5m": 300,
    "1h": 3600,
    "1d": 86400,
}


async def get_from_cache(r: Redis, cg_id: str, currency: str, timeframe: str) -> dict[str, list[tuple[int, int]]] | None:
    """
        Get data from cache
    """
    key = f"{cg_id}:{currency}:{timeframe}"
    raw_data = await r.get(key)
    if raw_data is None:
        return None
    data = json.loads(raw_data)
    return data


async def set_to_cache(r: Redis, cg_id: str, currency: str, timeframe: str, value: dict[str, list[tuple[int, int]]]):
    """
        Set data to cache, update expirations
    """
    key = f"{cg_id}:{currency}:{timeframe}"
    j_value = json.dumps(value)
    ex = expirations.get(timeframe)
    await r.set(key, j_value, ex=ex)
    lg.info(f"Updated cache for {cg_id}")


async def main():
    r = await Redis(host="0.0.0.0", port=6389)
    await r.set("test", "value", ex=2)
    tm = await r.ttl("test")
    lg.debug(tm)
    await asyncio.sleep(1)
    tm = await r.ttl("test")
    lg.debug(tm)
    await r.set("test", "value", ex=2)
    await asyncio.sleep(2)
    tm = await r.ttl("test")
    lg.debug(tm)
    res = await r.get("test")
    lg.debug(res)
    await r.aclose()

if __name__ == "__main__":
    asyncio.run(main())