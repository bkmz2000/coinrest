from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from ccxt.async_support.base.exchange import BaseExchange
from src.db.connection import AsyncSessionFactory
from src.db.crud import get_converter, get_cg_mapper
from src.lib.schema import TickerInfo
from src.lib.quotes import quote_mapper
from loguru import logger as lg

from src.lib import utils
from src.lib.utils import BaseMapper


class Converter:
    def __init__(self, exchange: BaseExchange):
        self.exchange = exchange
        self.mapper = None  # Mapper for mapping currencies to coingecko_id
        self.quote_mapper = quote_mapper
        self.converter = None  # Converter for mapping quote currencies to USD
        self._mapped = dict()  # Currency base, that already mapped for this exchange
        self.session = None
        self._attempt = 0
        self._success = 0
        self._max_volume = defaultdict(float)
        self._max_volume_price = defaultdict(float)

    async def init_converter(self, session: AsyncSession):
        self.mapper = await get_cg_mapper(session=session, exchange_id=self.exchange.id)
        self.converter = await get_converter(session=session)

    async def __aenter__(self):
        async with AsyncSessionFactory() as session:
            self.mapper = await get_cg_mapper(session=session, exchange_id=self.exchange.id)
            self.converter = await get_converter(session=session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        ...
        # await self.session.close()

    def _quote_to_cg_id(self, quote: str):
        usd_quote = self.quote_mapper.get(quote)
        if not usd_quote:
            usd_quote = self.mapper.get(quote)
        return usd_quote

    def _quote_to_usd(self, quote: str) -> float:
        """
            Convert quote currency to USD
        """
        if quote == "USD":
            return 1
        usd_quote = self.converter.get(quote)
        if not usd_quote:
            # lg.warning(f"{self.exchange.id} Cant convert {quote} to USD")
            usd_quote = 0
        return usd_quote


    def _get_quote_volume_usd(self, usd_quote: float, quote_volume: float) -> float:
        """
        Try to get USD volume by quote
        :param usd_quote: quote rate to USD
        :param quote_volume: quote amount
        :return: quote volume in USD
        """
        quote_volume_usd = 0
        if quote_volume and usd_quote:
            quote_volume_usd = usd_quote * quote_volume
        return quote_volume_usd

    def _get_base_volume_usd(self, usd_quote: float, base_volume: float, base_price: float) -> float:
        """
        Try to get USD volume by base
        :param base_price: amount of base price
        :param base_volume: volume of base price
        :param usd_quote: quote rate to USD
        :return: base volume converted to usd
        """
        base_volume_usd = 0
        if usd_quote and base_price and base_volume:
            base_volume_usd = base_price * base_volume * usd_quote
        return base_volume_usd

    def get_normalized_ticker(self, symbol: str, props: dict) -> TickerInfo | None:
        """
            Get ticker mapped to coingecko_id and converted to USD
        :param symbol: ticker symbol
        :param props: ticker properties
        :return:
        """
        if ":" in symbol or "/" not in symbol:
            return
        base_volume = props.get('baseVolume')
        quote_volume = props.get('quoteVolume')
        base_price = props.get("last")
        if not base_price or not (base_volume or quote_volume):
            return

        base, quote = symbol.split("/")
        usd_quote = self._quote_to_usd(quote)
        usd_base_price = usd_quote * base_price
        volume_usd = self._get_quote_volume_usd(usd_quote, quote_volume)
        if not volume_usd:
            volume_usd = self._get_base_volume_usd(usd_quote, base_volume, base_price)

        base_cg = self.mapper.get(base)
        quote_cg = self._quote_to_cg_id(quote)

        normalized_ticker = TickerInfo(
            exchange_id=self.exchange.id,
            base=base,
            base_cg=base_cg,
            quote=quote,
            quote_cg=quote_cg,
            price=base_price,
            price_usd=usd_base_price,
            base_volume=base_volume,
            quote_volume=quote_volume,
            volume_usd=volume_usd
        )
        return normalized_ticker
