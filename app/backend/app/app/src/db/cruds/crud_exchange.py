import datetime
from dataclasses import asdict

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, update, null, bindparam
from loguru import logger as lg

from src.db.models import Exchange, ExchangeMapper, Ticker
from src.lib.schema import ExchangeResponse, StrapiMarket, ExchangeNameResponse, TopExchangeResponse, PairsResponse, ExchangePair, TickerResponse, TickerInfo
from src.lib import utils


class ExchangeCRUD:
    async def get_exchange_names(self, session: AsyncSession):
        stmt = select(Exchange.ccxt_name.label("name")).where(Exchange.cg_identifier.is_not(null()))
        result = await session.execute(stmt)
        result = result.mappings()
        return [ExchangeNameResponse.model_validate(res) for res in result]

    async def get_exchanges(self, session: AsyncSession):
        stmt = select(Exchange.id, Exchange.cg_identifier).where(Exchange.cg_identifier.is_not(null()))
        result = await session.execute(stmt)
        result = result.mappings()
        return [ExchangeResponse.model_validate(res) for res in result]

    async def get_cg_ids(self, session: AsyncSession):
        stmt = select(Exchange.cg_identifier).where(Exchange.cg_identifier.is_not(null()))
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result

    async def update_many(self, session: AsyncSession, exchanges: list[StrapiMarket]):
        stmt = insert(Exchange).values([ex.model_dump() for ex in exchanges])
        do_update = stmt.on_conflict_do_update(
            index_elements=[Exchange.ccxt_name],
            set_=dict(
                cg_identifier=stmt.excluded.cg_identifier,
                centralized=stmt.excluded.centralized,
                trust_score=stmt.excluded.trust_score,
                logo=stmt.excluded.logo,
                is_active=stmt.excluded.is_active,
                full_name=stmt.excluded.full_name
            )
        )
        await session.execute(do_update)
        await session.commit()

    async def save_mappings(self, session: AsyncSession, exchange_id: int, mapped: dict):
        now = datetime.datetime.now()
        mapping_list = [dict(exchange_id=exchange_id, symbol=symbol, cg_id=gecko, updated_at=now) for symbol, gecko in mapped.items()]
        stmt = insert(ExchangeMapper).values(mapping_list)
        update = stmt.on_conflict_do_update(
            index_elements=[ExchangeMapper.exchange_id, ExchangeMapper.symbol],
            set_=dict(
                symbol=stmt.excluded.symbol,
                cg_id=stmt.excluded.cg_id,
                updated_at=now
            )
        )
        await session.execute(update)
        await session.commit()

    async def get_top_exchanges(self, session: AsyncSession, limit: int) -> list[TopExchangeResponse]:
        top_trust = (
            select(Exchange.trust_score)
            .where(Exchange.trust_score.is_not(null()))
            .order_by(Exchange.trust_score.desc())
            .limit(limit+10)  # +10 reserve for exchanges without tickers
        ).subquery()
        top_trust_distinct = select(top_trust).distinct().scalar_subquery()

        max_trust_exs = select(Exchange.id, Exchange.trust_score, Exchange.full_name).where(
            Exchange.trust_score.in_(top_trust_distinct)).subquery()

        exs_with_top_volume = (
            select(
                max_trust_exs.c.full_name.label("name"),
                max_trust_exs.c.trust_score,
                func.sum(Ticker.volume_usd).label("volume_24h"),
            )
            .join(
                Ticker, Ticker.exchange_id == max_trust_exs.c.id
            )
            .group_by(
                max_trust_exs.c.full_name,
                max_trust_exs.c.trust_score
            ).order_by(
                max_trust_exs.c.trust_score.desc(),
                func.sum(Ticker.volume_usd).desc()
            ).limit(limit))

        result = await session.execute(exs_with_top_volume)
        result = result.mappings()
        result = [TopExchangeResponse.model_validate(exchange) for exchange in result]
        return result
    
    async def get_pairs(self, session: AsyncSession, exchange_name: str) -> PairsResponse:
        id_req = select(Exchange.id).where(Exchange.ccxt_name == exchange_name)
        exchange_id = (await session.execute(id_req)).scalar_one_or_none()

        lg.debug(f"req = {str(id_req)} id = {exchange_id} end")

        pairs_req = select(Ticker).where(Ticker.exchange_id == exchange_id)

        result = await session.execute(pairs_req)
        lines = result.scalars().all()

        ex_pairs: list[ExchangePair] = []

        for line in lines:
            base = line.base
            quote = line.quote
            price = line.price
            volume_usd = line.volume_usd
            ex_pairs.append(ExchangePair(
                base=base,
                quote=quote,
                price=price,
                volume=volume_usd
            ))


        return PairsResponse(exchange_id=exchange_name, pairs=ex_pairs)


    async def get_most_trusted(self, session: AsyncSession) -> list[str]:
        stmt = select(Exchange.ccxt_name).where(Exchange.trust_score > 5)
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result

    async def get_all_exchanges(self, session: AsyncSession) -> list[str]:
        stmt = select(Exchange.ccxt_name)
        result = await session.execute(stmt)
        result = result.scalars().all()
        return result

    async def check_is_active(self, session: AsyncSession, ex_name: str):
        stmt = select(Exchange).where(Exchange.ccxt_name == ex_name).where(Exchange.is_active == True)
        result = await session.execute(stmt)
        result = result.scalar_one_or_none()
        return result

    async def create(self, session: AsyncSession, exchange: utils.CreateExchange):
        await session.execute(insert(Exchange).values(asdict(exchange)))
        await session.commit()
        lg.info(f"New exchange {exchange.ccxt_name} created in db")