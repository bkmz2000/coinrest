from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from src.db import connection
from src.db.crud import get_fiat_currency_rate
from src.db.cruds.crud_ticker import TickerCRUD
from src.db.cruds.crud_last import LastCRUD
from src.lib.schema import MarketResponse, CoinResponse, NewCoinResponse
from loguru import logger as lg

router = APIRouter()


@router.get("/exchanges", response_model=MarketResponse)
async def get_ticker_exchanges(hdr_id: str,
                               limit: int = Query(100),
                               offset: int = Query(0),
                               currency: Literal['AUD', 'BRL', 'BTC', 'CAD', 'CHF', 'CNY', 'CZK', 'EUR', 'GBP', 'IDR', 'INR', 'JPY', 'KRW', 'KZT', 'MXN', 'MYR', 'NOK', 'NZD', 'PHP', 'PLN', 'RUB', 'SEK', 'SGD', 'TRY', 'USD', 'ZAR'] = Query('USD'),
                               quote_currency: str = Query('All', description="Use 'All' for all currencies or ex.: 'BTC', 'USDT' "),
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
    coins, total = await crud.exchanges_by_cg_id(cg_id=hdr_id,
                                                 limit=limit,
                                                 offset=offset,
                                                 quote_currency=quote_currency,
                                                 exchange_type=exchange_type,
                                                 trading_type=trading_type,
                                                 id_sort=id_sort,
                                                 exchange_sort=exchange_sort,
                                                 pair_sort=pair_sort,
                                                 price_sort=price_sort,
                                                 volume_sort=volume_sort,
                                                 session=session)
    rate = 1
    if currency != "USD":
        rate = await get_fiat_currency_rate(session=session, currency=currency)
    result = []
    quotes = set()
    for coin in coins:
        result.append(CoinResponse(
            id=coin['id'],
            exchange=coin['full_name'],
            logo=coin['logo'],
            pair=coin['base'] + '/' + coin['quote'],
            price=coin['price_usd'] * rate,
            volume_24h=coin['volume_usd'] * rate,
            exchange_type="CEX" if coin['centralized'] else "DEX",
            trading_type="Spot"
        ))
        quotes.add(coin['quote'])
    return MarketResponse(
        coins=result,
        total=total,
        quotes=tuple(quotes)
    )


@router.get("/lost")
async def lost_coins(session: AsyncSession = Depends(connection.get_db)):
    crud = LastCRUD()
    return await crud.get_lost_coins(session=session)


@router.get("/quotes", response_model=list[str])
async def lost_coins(hdr_id: str, session: AsyncSession = Depends(connection.get_db)):
    crud = TickerCRUD()
    return await crud.get_coin_quotes(session=session, hdr_id=hdr_id)


@router.get("/new", response_model=list[NewCoinResponse])
async def get_new_coins(session: AsyncSession = Depends(connection.get_db)):
    """
        Get new coins
    """
    last_crud = LastCRUD()
    return await last_crud.get_new_coins(session=session)
