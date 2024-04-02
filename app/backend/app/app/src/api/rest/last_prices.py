from sqlalchemy.ext.asyncio import AsyncSession

from src.db.cruds.crud_last import LastCRUD
from src.lib import schema


async def get_coins(session: AsyncSession) -> dict[str, schema.PriceResponse]:
    crud = LastCRUD()
    coins = await crud.get_coins_from_db(session=session)
    result = {}
    for coin in coins:
        result[coin.cg_id] = schema.PriceResponse(usd=coin.price_usd,
                                                 usd_24h_vol=coin.volume_usd,
                                                 btc=coin.price_btc,
                                                 btc_24h_vol=coin.volume_btc,
                                                 )
    return result