from sqlalchemy.ext.asyncio import AsyncSession
from src.lib.utils import CoinResponse

from src.db.crud import get_coins_from_db
from src.lib import utils



async def get_coins(session: AsyncSession) -> dict[str, CoinResponse]:
    coins = await get_coins_from_db(session=session)
    result = {}
    for coin in coins:
        result[coin.cg_id] = utils.CoinResponse(usd=coin.price_usd,
                                                usd_24h_vol=coin.volume_usd,
                                                btc=coin.price_btc,
                                                btc_24h_vol=coin.volume_btc,
                                                )
    return result
