import asyncio
from collections import defaultdict
from src.db.connection import AsyncSessionFactory
from src.db.crud import get_all_tickers, save_last
from loguru import logger as lg
import scipy.stats as stats
import numpy as np

from src.lib.schema import CoinInput, CoinOutput


async def main():
    lg.info("Start last values calculation")
    try:
        async with AsyncSessionFactory() as session:
            tickers = await get_all_tickers(session=session)
            coins = defaultdict(CoinInput)
            result = []

            for ticker in tickers:
                coins[ticker.cg_id].price = np.append(coins[ticker.cg_id].price, ticker.price_usd)
                coins[ticker.cg_id].volume = np.append(coins[ticker.cg_id].volume, ticker.volume_usd)

            btc_coin = calculate_bitcoin_values('bitcoin', coins['bitcoin'])

            result.append(CoinOutput(
                cg_id=btc_coin.cg_id,
                price_usd=btc_coin.price_usd,
                price_btc=btc_coin.price_btc,
                volume_usd=btc_coin.volume_usd,
                volume_btc=btc_coin.volume_btc
            ))

            for cg_id, arrays in coins.items():
                if cg_id == 'bitcoin':
                    continue
                # calculate z-score for every price
                z = np.abs(stats.zscore(arrays.price))
                # delete all outliers from prices and volumes arrays
                clean_data_prices = np.delete(arrays.price, np.where(z >= 3))
                clean_data_volumes = np.delete(arrays.volume, np.where(z >= 3))
                # calculate weighted average
                avg_price_usd = np.average(clean_data_prices, weights=clean_data_volumes)
                # calculate sum of all volumes
                sum_volumes_usd = np.sum(arrays.volume)

                result.append(CoinOutput(
                    cg_id=cg_id,
                    price_usd=avg_price_usd,
                    price_btc=np.divide(avg_price_usd, btc_coin.price_usd),
                    volume_usd=sum_volumes_usd,
                    volume_btc=np.divide(sum_volumes_usd, btc_coin.price_usd)
                ))

            # for coin in result:
            #     print(coin)
            await save_last(session=session, coins=result)
    except Exception as e:
        lg.error(f"Last values calculation failed: {e}")


def calculate_bitcoin_values(cg_id, arrays: CoinInput) -> CoinOutput:
    # calculate z-score for every price
    z = np.abs(stats.zscore(arrays.price))
    # delete all outliers from prices and volumes arrays
    clean_data_prices = np.delete(arrays.price, np.where(z >= 3))
    clean_data_volumes = np.delete(arrays.volume, np.where(z >= 3))
    # calculate weighted average
    avg_price_usd = np.average(clean_data_prices, weights=clean_data_volumes)
    # calculate sum of all volumes
    sum_volumes_usd = np.sum(arrays.volume)

    return CoinOutput(
        cg_id=cg_id,
        price_usd=avg_price_usd,
        price_btc=1,
        volume_usd=sum_volumes_usd,
        volume_btc=np.divide(sum_volumes_usd, avg_price_usd)
    )


if __name__ == "__main__":
    asyncio.run(main())
