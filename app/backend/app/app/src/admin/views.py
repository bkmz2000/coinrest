from datetime import datetime

from sqladmin import Admin, ModelView
from src.db.models import Exchange, Ticker
from loguru import logger as lg


class ExchangesAdmin(ModelView, model=Exchange):
    column_list = [Exchange.ccxt_name, Exchange.full_name, Exchange.trust_score, Exchange.centralized]
    column_details_list = "__all__"

    column_searchable_list = [Exchange.ccxt_name]
    column_sortable_list = [Exchange.ccxt_name, Exchange.trust_score]


class TickerAdmin(ModelView, model=Ticker):
    def date_format(value):
        return datetime.utcfromtimestamp(value)

    column_list = [Ticker.base, Ticker.base_cg, Ticker.quote, Ticker.quote_cg, Ticker.price_usd, Ticker.volume_usd, Ticker.last_update]
    column_types = dict(ModelView.column_type_formatters, last_update=date_format)
    save_as = True

    column_searchable_list = [Ticker.base, Ticker.quote]
