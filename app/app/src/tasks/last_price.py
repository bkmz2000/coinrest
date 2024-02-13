from collections import defaultdict
from loguru import logger as lg

from src.db.crud import save_last_volumes
from src.deps.markets import AllMarketsLoader
from src.mapper import get_cg_ids
from src.lib import utils
from src.db.connection import AsyncSessionFactory


async def main():
    exs = AllMarketsLoader()
    await exs.start()
    ex_markets = exs.get_target_markets(target="volume")
    async with AsyncSessionFactory() as session:
        coins = defaultdict(utils.Coin)
        prices = {}
        super_total = 0

        for ex in ex_markets:
            try:
                ids = await get_cg_ids(session=session, exchange_id=ex.id)
                tickers = await ex.fetch_tickers()
                total = 0

                # Определяем все монеты по которым мы можем найти курс в тезерах
                for k, v in tickers.items():
                    if k.endswith("/USDT"):
                        base = k.split("/USDT")[0]
                        if v['last']:
                            prices[base] = v['last']

                # Перебираем все монеты, высчитаваем volume по курсу определенному выше
                for k, v in tickers.items():
                    if ":" in k:
                        continue
                    base = k.split("/")[0]
                    rate = prices.get(base)
                    volume = v.get('baseVolume')
                    if rate and volume:
                        cg_id = ids.get(base + "/USDT")
                        if cg_id:
                            coins[cg_id].volume += (volume * rate)
                            coins[cg_id].price = rate
                            if base == "BTC":
                                total += volume * rate
                                super_total += volume * rate
                                lg.info(f"{ex.id}-{k}: {volume * rate}, {total}")
                lg.info(f"Total for {ex.id}: {total}")
            except Exception as e:
                lg.error(e)
        await save_last_volumes(session=session, coins=coins)
        # for k, v in coins.items():
        #     lg.info(f"{k}: {v}")
        lg.info(super_total)
        await exs.close()