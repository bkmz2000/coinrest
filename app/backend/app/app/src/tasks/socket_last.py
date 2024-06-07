import asyncio
import os
import sys
import traceback

from loguru import logger as lg

import aiohttp
from src.lib import utils
from src.db.crud import save_socket_last_info
from src.db.connection import AsyncSessionFactory

SOCKET_URL = os.environ.get("SOCKET_URL", "https://api2.hodler.sh/ws")


async def get_socket_last() -> list[utils.SocketUpdated]:
    """Get last prices and last update time from socket service"""
    url = SOCKET_URL + "/last_update"
    result = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp and resp.status == 200:
                data = await resp.json()
                for coin in data:
                    result.append(utils.SocketUpdated(
                        cg_id=coin["hodler_id"],
                        price_usd=coin["price"],
                        exchange=coin["exchange"],
                        updated_at=coin["updated_at"],
                    ))
    return result


async def main() -> None:
    lg.info("Fetching last socket values")
    try:
        last_values = await get_socket_last()
        async with AsyncSessionFactory() as session:
            await save_socket_last_info(session=session, coins=last_values)
        lg.info("Socket info updated")
    except Exception as e:
        lg.error(e.with_traceback(traceback.print_exc(100, sys.stdout)))


if __name__ == "__main__":
    asyncio.run(main())
