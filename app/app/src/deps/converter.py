from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession
from ccxt.async_support.base.exchange import BaseExchange
from src.db.connection import AsyncSessionFactory
from src.db.crud import get_exchange_cg_ids, get_converter, set_mapper_data, get_cg_mapper
from loguru import logger as lg

from src.lib import utils
from src.lib.utils import BaseMapper


class Converter:
    def __init__(self, exchange: BaseExchange, geckos: list | None = None):
        self.exchange = exchange
        self.mapper = None  # Mapper for mapping currencies to coingecko_id
        self.converter = None  # Converter for mapping quote currencies to USD
        self.geckos = geckos  # Init with geckos if u want to start new mapping
        self._mapped = dict()  # Currency base, that already mapped for this exchange
        self.session = None
        self._attempt = 0
        self._success = 0
        self._max_volume = defaultdict(float)
        self._max_volume_price = defaultdict(float)


    async def __aenter__(self):
        self.session = AsyncSessionFactory()
        self.mapper = await get_cg_mapper(session=self.session, exchange_id=self.exchange.id)
        self.converter = await get_converter(session=self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()


    def _quote_to_usd(self, quote: str):
        """
            Convert quote currency to USD
        """
        if quote == "USD":
            return 1
        usd_quote = self.converter.get(quote)
        if not usd_quote:
            lg.warning(f"Cant convert {quote} to USD")
        return usd_quote

    def _map_cg_id(self, base: str, price: float) -> str:
        """
            Searching the same symbol and price
        """
        for coin in self.geckos:
            if coin["symbol"] == base:
                if 0.7 <= coin["quote"]["USD"]["price"] / price <= 1.3:
                    return coin["cgid"]

    async def match_and_save(self, symbol, price):
        """
            Match symbol with current price to coingecko_id, and store to db
        :param price: last price from ticker
        :param symbol: ex. BTC/USDT, ETH/EUR, ...
        :return: None
        """
        if not self.geckos:
            raise ValueError("Actual coingecko prices not downloaded")
        if ":" in symbol or "/" not in symbol:  # ':' or no '/' - means derivative, so skip it.
            return
        base, quote = symbol.split("/")
        if base in self._mapped:
            return
        if not price:
            return
        usd_quote = self._quote_to_usd(quote)
        if usd_quote:
            self._attempt += 1
            usd_price = price * usd_quote
            cg_id = self._map_cg_id(base, usd_price)
            if cg_id:
                self._success += 1
                self._mapped[base] = cg_id
                await self._store_to_db(cg_id, base)
            lg.info(f"{self._success}/{self._attempt}: {symbol} {cg_id}  *{usd_price:,}*")

    async def _store_to_db(self, cg_id: str, base: str):
        mapper = BaseMapper(cg_id=cg_id, exchange=self.exchange.id, symbol=base)
        await set_mapper_data(session=self.session, mapper=mapper)

    def get_volumes(self, symbol: str, props: dict, coins: dict[str, utils.Coin]):
        if ":" in symbol or "/" not in symbol:
            return
        quote_volume_usd = 0
        base_volume_usd = 0
        base, quote = symbol.split("/")
        base_volume = props.get('baseVolume')
        if not base_volume:
            base_volume = 0

        quote_volume = props.get('quoteVolume')
        if not quote_volume:
            quote_volume = 0

        usd_quote = self._quote_to_usd(quote)
        if usd_quote:
            quote_volume_usd = usd_quote * quote_volume

        base_price = props.get("last")
        if base_price and usd_quote:
            base_volume_usd = base_price * base_volume * usd_quote
        base_cg = self.mapper.get(base)
        quote_cg = self.mapper.get(quote)
        # lg.info(f"{base_cg}: {base_volume_usd}, {quote_cg}: {quote_volume_usd}")

        if base_cg:
            if base_volume_usd > self._max_volume[base_cg]:
                self._max_volume[base_cg] = base_volume_usd
                self._max_volume_price[base_cg] = base_price * usd_quote
            coins[base_cg].exchange = self.exchange.id
            coins[base_cg].volume += base_volume_usd
            coins[base_cg].price = self._max_volume_price[base_cg]

        if quote_cg:
            coins[quote_cg].exchange = self.exchange.id
            coins[quote_cg].volume += quote_volume_usd
