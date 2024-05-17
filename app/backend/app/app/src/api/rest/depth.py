import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from src.db import crud
from src.lib import schema
from src.db.connection import AsyncSessionFactory


async def get_depth(session: AsyncSession, cg_id: str, depth: int) -> schema.MarketDepthResponse | None:
    orders = await crud.get_order_books(cg_id=cg_id, session=session)
    if not orders:
        return
    bid_depth_value = orders.last_price - (orders.last_price * depth / 100)
    ask_depth_value = orders.last_price + (orders.last_price * depth / 100)

    bids = []
    bid_volume = 0
    asks = []
    ask_volume = 0

    for bid in orders.bids:
        if orders.last_price >= float(bid[0]) >= bid_depth_value:
            bids.append(schema.Bid(
                price=bid[0],
                qty=bid[1],
            ))
            bid_volume += bid[0] * bid[1]

    for ask in orders.asks:
        if orders.last_price <= float(ask[0]) <= ask_depth_value:
            asks.append(schema.Ask(
                price=ask[0],
                qty=ask[1],
            ))
            ask_volume += ask[0] * ask[1]

    result = schema.MarketDepthResponse(
        exchange=orders.exchange,
        coin_id=orders.cg_id,
        symbol=orders.base + "/" + orders.quote,
        bids_volume=bid_volume,
        asks_volume=ask_volume,
        depth_chart=schema.DepthChart(
            bids=strict_array(bids),
            asks=strict_array(asks),
        )
    )
    return result


def strict_array(arr: list[schema.Ask | schema.Bid]) -> list[schema.Ask | schema.Bid]:
    max_number = 100
    if len(arr) <= max_number:
        return arr
    aggregate = len(arr) // max_number
    return arr[::aggregate]

async def main():
    async with AsyncSessionFactory() as session:
        ...
        await get_depth(session=session, cg_id="ethereum", depth=2)

if __name__ == '__main__':
    asyncio.run(main())