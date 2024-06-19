import asyncio
import datetime
import time
from collections import defaultdict

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, null, union_all, text

from src.db.connection import AsyncSessionFactory
from src.db.models import Ticker, Exchange, QuoteMapper, TopVolume
from src.lib import utils
from src.lib.schema import TickerResponse, MappedCoinResponse
from src.lib.utils import CoinWithPrice, CoinWithPriceAndDate


class TickerCRUD:
    async def get_tickers(self, session: AsyncSession, limit: int, offset: int) -> list[str]:
        stmt = select(Ticker.base_cg).group_by(Ticker.base_cg).order_by(func.sum(Ticker.volume_usd).desc()).limit(
            limit).offset(offset)
        result = await session.execute(stmt)
        result = result.scalars().all()

        return result

    async def get_ticker_by_exchange(self, session: AsyncSession, exchange_name: str):
        stmt = (
            select(Exchange.ccxt_name.label("name"),
                   Ticker.base,
                   Ticker.quote,
                   Ticker.base_cg,
                   Ticker.price_usd,
                   Ticker.volume_usd,
                   Ticker.last_update)
            .join(Exchange, Exchange.id == Ticker.exchange_id)
            .where(Exchange.ccxt_name == exchange_name)
            .order_by(Ticker.volume_usd.desc())
        )
        result = await session.execute(stmt)
        result = result.mappings()
        return [TickerResponse.model_validate(res) for res in result]

    async def get_ticker_by_cg(self, session: AsyncSession, cg_id: str):
        stmt = (
            select(Exchange.ccxt_name.label("name"),
                   Ticker.base_cg,
                   Ticker.base,
                   Ticker.quote,
                   Ticker.price_usd,
                   Ticker.volume_usd,
                   Ticker.last_update
                   )
            .join(Exchange, Exchange.id == Ticker.exchange_id)
            .filter(or_(Ticker.base_cg == cg_id, Ticker.quote_cg == cg_id))
            .order_by(Ticker.volume_usd.desc())
        )
        result = await session.execute(stmt)
        result = result.mappings()
        return [TickerResponse.model_validate(res) for res in result]

    async def get_top_tickers(self, session: AsyncSession):
        unix_stamp_now = int(time.time()) - 10800  # 3 hours
        base_volume = (select(Ticker.base_cg.label("gecko"), func.sum(Ticker.volume_usd).label("volume_usd"))
                       .where(Ticker.last_update >= unix_stamp_now)
                       .group_by(Ticker.base_cg).select_from(Ticker))

        quote_volume = (select(Ticker.quote_cg.label("gecko"), func.sum(Ticker.volume_usd).label("volume_usd"))
                        .where(Ticker.last_update >= unix_stamp_now)
                        .group_by(Ticker.quote_cg).select_from(Ticker))

        stmt = (
            base_volume.union_all(quote_volume).subquery()
        )
        new_stmt = (
            select
                (
                stmt.c.gecko.label("base_cg"),
                func.sum(stmt.c.volume_usd).label("volume_usd")
            )
            .group_by(stmt.c.gecko)
            .select_from(stmt)
            .order_by(func.sum(stmt.c.volume_usd).desc())
            .limit(250)
        )
        result = await session.execute(new_stmt)
        result = result.mappings()
        return [dict(res) for res in result]

    async def exchanges_by_cg_id(self,
                                 cg_id: str,
                                 limit: int,
                                 offset: int,
                                 quote_currency: str,
                                 exchange_type: str,
                                 trading_type: str,
                                 id_sort: str,
                                 exchange_sort,
                                 pair_sort,
                                 price_sort,
                                 volume_sort,
                                 session: AsyncSession):
        stmt = (select(Exchange.id,
                       Exchange.full_name,
                       Exchange.logo,
                       Ticker.base,
                       Ticker.quote,
                       Ticker.price_usd,
                       Ticker.volume_usd,
                       Exchange.centralized)
                .join(Exchange, Exchange.id == Ticker.exchange_id)
                .where(Ticker.base_cg == cg_id)
                .where(Ticker.price_usd > 0)
                .where(Ticker.volume_usd > 0)
                )

        if quote_currency != "All":
            stmt = stmt.filter(Ticker.quote == quote_currency)

        if exchange_type != "All":
            if exchange_type == "CEX":
                stmt = stmt.filter(Exchange.centralized == True)
            elif exchange_type == "DEX":
                stmt = stmt.filter(Exchange.centralized == False)

        stmt = self.trading_type_filter(stmt, trading_type)
        stmt = self.ex_id_order(stmt, id_sort)
        stmt = self.ex_exchange_order(stmt, exchange_sort)
        stmt = self.t_pair_order(stmt, pair_sort)
        stmt = self.t_price_order(stmt, price_sort)
        stmt = self.t_volume_order(stmt, volume_sort)

        count_all = select(func.count(stmt.c.id)).select_from(stmt)
        count = await session.execute(count_all)
        count = count.scalar()

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        result = result.mappings()

        return [dict(res) for res in result], count

    def trading_type_filter(self, stmt: select, trading_type: str):
        if trading_type == "Spot":
            return stmt
            # return stmt.filter(Ticker.trading_type == trading_type)
        else:
            return stmt.filter(sqlalchemy.false())

    def ex_id_order(self, stmt: select, id_sort: str):
        if id_sort == "ASC":
            return stmt.order_by(Exchange.id)
        elif id_sort == "DESC":
            return stmt.order_by(Exchange.id.desc())
        return stmt

    def ex_exchange_order(self, stmt: select, exchange_sort: str):
        if exchange_sort == "ASC":
            return stmt.order_by(Exchange.full_name)
        elif exchange_sort == "DESC":
            return stmt.order_by(Exchange.full_name.desc())
        return stmt

    def t_pair_order(self, stmt: select, pair_sort: str):
        if pair_sort == "ASC":
            return stmt.order_by(Ticker.quote)
        elif pair_sort == "DESC":
            return stmt.order_by(Ticker.quote.desc())
        return stmt

    def t_price_order(self, stmt: select, price_sort: str):
        if price_sort == "ASC":
            return stmt.order_by(Ticker.price_usd)
        elif price_sort == "DESC":
            return stmt.order_by(Ticker.price_usd.desc())
        return stmt

    def t_volume_order(self, stmt: select, volume_sort: str):
        if volume_sort == "ASC":
            return stmt.order_by(Ticker.volume_usd)
        elif volume_sort == "DESC":
            return stmt.order_by(Ticker.volume_usd.desc())
        return stmt

    async def get_all_tickers(self, session: AsyncSession) -> list[utils.TickerSimple]:
        """
        Get all base ticker with their prices and volumes. And get all quote tickers with their volumes only
        """
        unix_stamp_now = int(time.time()) - 10800  # 3 hours

        as_date = datetime.datetime.utcfromtimestamp(unix_stamp_now)

        base_cg_prices = (
            select(Ticker.base_cg.label("cg_id"), Ticker.price_usd.label("price_usd"), Ticker.volume_usd)
            .where(Ticker.base_cg.is_not(null()))
            .where(Ticker.price_usd > 0)
            .where(Ticker.volume_usd > 0)
            .where(Ticker.last_update > unix_stamp_now)
        )
        quote_cg_prices = (
            select(Ticker.quote_cg.label("cg_id"), QuoteMapper.rate.label("price_usd"), Ticker.volume_usd)
            .where(Ticker.quote == QuoteMapper.currency)
            .where(QuoteMapper.update_at > as_date)
            .where(Ticker.quote_cg.is_not(null()))
            .where(Ticker.volume_usd > 0)
            .where(Ticker.last_update > unix_stamp_now)
        )

        stmt = union_all(base_cg_prices, quote_cg_prices).order_by(Ticker.volume_usd.desc())

        result = await session.execute(stmt)
        result = result.mappings()
        result = [utils.TickerSimple.model_validate(res) for res in result]
        return result

    async def get_actual_coins(self, session: AsyncSession):
        unix_stamp_now = int(time.time()) - 10800  # 3 hours
        stmt = (select(Ticker.base_cg)
                .group_by(Ticker.base_cg)
                .having(func.max(Ticker.last_update) > unix_stamp_now)
                .order_by(func.max(Ticker.last_update).desc())
                )
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result

    async def get_prices_by_symbol(self, session: AsyncSession, symbol: str):
        unix_stamp_now = int(time.time()) - 10800  # 3 hours

        stmt = ((select(Ticker.base_cg.label("cg_id"), Ticker.price_usd, Ticker.created_at)
                 .where(Ticker.base == symbol)
                 .where(Ticker.last_update > unix_stamp_now)))
        result = await session.execute(stmt)
        result = result.mappings()
        result = [CoinWithPriceAndDate.model_validate(res) for res in result]
        return result

    async def save_max_volume_tickers(self, session: AsyncSession):
        """
            Calculate max_volume for every coin and store to table
        """
        stmt = text(
            """
                WITH base_ranked_rows AS (
                    SELECT *,
                           ROW_NUMBER() OVER(PARTITION BY base_cg ORDER BY volume_usd DESC) AS rn
                    FROM public.ticker WHERE base_cg IS NOT NULL AND last_update > :last_update
                ), 
                quote_ranked_rows AS (
                    SELECT *,
                           ROW_NUMBER() OVER(PARTITION BY quote_cg ORDER BY volume_usd DESC) AS rn
                    FROM public.ticker WHERE quote_cg IS NOT NULL AND last_update > :last_update
                ),
                new_ranked_rows AS (
                    SELECT *,
                           ROW_NUMBER() OVER(PARTITION BY cg_id ORDER BY volume_usd DESC) AS rn
                    FROM (SELECT cg_id, base, quote, volume_usd, ccxt_name FROM (
                        SELECT base_cg AS cg_id, base, quote, volume_usd, ex.ccxt_name
                        FROM base_ranked_rows brr, exchange ex
                        WHERE rn = 1 AND ex.id = brr.exchange_id
                        UNION
                        SELECT quote_cg AS cg_id, base, quote, volume_usd, ex.ccxt_name
                        FROM quote_ranked_rows qrr, exchange ex
                        WHERE rn = 1 AND ex.id = qrr.exchange_id
                ) un ORDER BY volume_usd DESC
                ) new_)
                INSERT INTO top_volume(cg_id, base, quote, volume_usd, exchange)
                    SELECT cg_id, base, quote, volume_usd, ccxt_name FROM new_ranked_rows
                    WHERE rn = 1 
                ON CONFLICT ON CONSTRAINT unique_coin_id
                DO UPDATE SET 
                    volume_usd = EXCLUDED.volume_usd,
                    exchange = EXCLUDED.exchange,
                    updated_at = now()
	        """
        )
        parameters = {"last_update": int(time.time()) - 10800}  # 3 hours
        await session.execute(stmt, params=parameters)
        await session.commit()

    async def get_coin_with_max_volume(self, session: AsyncSession, cg_id: str):
        max_vol_subq = select(func.max(Ticker.volume_usd)).where(
            or_(Ticker.base_cg == cg_id, Ticker.quote_cg == cg_id)).scalar_subquery()
        stmt = (
            select(Ticker.base_cg, Ticker.quote_cg, Ticker.base, Ticker.quote, Exchange.full_name, Exchange.ccxt_name)
            .where(Ticker.volume_usd == max_vol_subq)
            .where(Ticker.exchange_id == Exchange.id)
        ).limit(1)
        result = await session.execute(stmt)
        result = result.mappings()
        result = [dict(res) for res in result]
        if result:
            return result[0]

    async def get_exchange_coins_for_orderbook(self, session: AsyncSession, exchange: str) -> list[utils.OrderBookCoin]:
        """
            Get all orderbook pairs for specified exchange
        """
        stmt = (select(TopVolume.cg_id,
                       func.concat(TopVolume.base + "/" + TopVolume.quote).label("symbol"))
                .group_by(TopVolume.cg_id, TopVolume.base, TopVolume.quote)
                .where(TopVolume.exchange == exchange))
        result = await session.execute(stmt)
        result = result.mappings()
        result = [utils.OrderBookCoin.model_validate(res) for res in result]
        return result

    async def get_depth_exchanges(self, session: AsyncSession):
        """
            Get all exchanges for fetching order books
        """
        stmt = select(TopVolume.exchange).distinct()
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result

    async def get_mapper(self, session: AsyncSession, exchange_ids: list[str]) -> dict[str, list[MappedCoinResponse]]:
        stmt = (
            select(Ticker.base, Ticker.base_cg, Exchange.ccxt_name)
            .where(Ticker.exchange_id == Exchange.id)
            .where(Ticker.quote_cg == 'tether')
            .where(Ticker.base_cg.is_not(null()))
            .where(Exchange.ccxt_name.in_(exchange_ids))
        )
        result = await session.execute(stmt)
        result = result.mappings()
        exs_dict = defaultdict(list)
        for res in result:
            exs_dict[res["ccxt_name"]].append(MappedCoinResponse(
                base=res["base"],
                hdr_id=res["base_cg"]
            )

            )
        return exs_dict


    async def get_coin_quotes(self, session: AsyncSession, hdr_id: str) -> list[str]:
        stmt = select(Ticker.quote.distinct()).where(Ticker.base_cg == hdr_id)
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result


async def main():
    async with AsyncSessionFactory() as session:
        cr = TickerCRUD()
        await cr.get_depth_exchanges(session)
        # await cr.save_max_volume_tickers(session)


if __name__ == "__main__":
    asyncio.run(main())
