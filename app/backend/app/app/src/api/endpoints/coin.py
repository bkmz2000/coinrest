from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from src.db import connection
from src.db.cruds.crud_ticker import TickerCRUD
from src.lib.schema import MarketResponse, CoinResponse
from loguru import logger as lg

router = APIRouter()


@router.get("/exchanges", response_model=MarketResponse)
async def get_ticker_exchanges(cg_id: str,
                               limit: int = Query(100),
                               offset: int = Query(0),
                               currency: Literal['All', 'USDT', 'BTC'] = Query('All'),
                               exchange_type: Literal['All', 'CEX', 'DEX'] = Query('All'),
                               trading_type: Literal['Spot', 'Perpetual', 'Futures'] = Query('Spot'),
                               id_sort: Literal['NO', 'ASC', 'DESC'] = Query('NO'),
                               exchange_sort: Literal['NO', 'ASC', 'DESC'] = Query('NO'),
                               pair_sort: Literal['NO', 'ASC', 'DESC'] = Query('NO'),
                               price_sort: Literal['NO', 'ASC', 'DESC'] = Query('NO'),
                               volume_sort: Literal['NO', 'ASC', 'DESC'] = Query('NO'),
                               session: AsyncSession = Depends(connection.get_db)):
    """
        Get coin exchanges
    """
    crud = TickerCRUD()
    coins, total = await crud.exchanges_by_cg_id(cg_id=cg_id,
                                                 limit=limit,
                                                 offset=offset,
                                                 currency=currency,
                                                 exchange_type=exchange_type,
                                                 trading_type=trading_type,
                                                 id_sort=id_sort,
                                                 exchange_sort=exchange_sort,
                                                 pair_sort=pair_sort,
                                                 price_sort=price_sort,
                                                 volume_sort=volume_sort,
                                                 session=session)
    result = []
    quotes = set()
    for coin in coins:
        result.append(CoinResponse(
            id=coin['id'],
            exchange=coin['full_name'],
            pair=coin['base'] + '/' + coin['quote'],
            price=coin['price_usd'],
            volume_24h=coin['volume_usd'],
            exchange_type="CEX" if coin['centralized'] else "DEX",
            trading_type="Spot"
        ))
        quotes.add(coin['quote'])
    return MarketResponse(
        coins=result,
        total=total,
        quotes=tuple(quotes)
    )
