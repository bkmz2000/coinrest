import asyncio
import time
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.connection import AsyncSessionFactory
from src.db.cruds.crud_historical import HistoricalCRUD
from src.db.crud import get_fiat_currency_rate
from src.lib import schema

CHART = {
    "24h":
        {
            "limit": 288,
            "type": "5_minute",
            "step": 300,
        },
    "7d": {
        "limit": 168,
        "type": "hourly",
        "step": 3600,
    },
    "14d": {
        "limit": 336,
        "type": "hourly",
        "step": 3600,
    },
    "1M": {
        "limit": 720,
        "type": "hourly",
        "step": 3600,
    },
    "3M": {
        "limit": 90,
        "type": "daily",
        "step": 86400,
    },
    "1Y": {
        "limit": 365,
        "type": "daily",
        "step": 86400,
    }
}


async def get_charts(exchange_name: str,
                     period: Literal['24h', '7d', '14d', '1M', '3M', '1Y'],
                     currency: str,
                     session: AsyncSession) -> schema.ExchangeChartResponse:
    """
        Get exchanges volumes chart
    """
    chart_params = CHART.get(period)
    historical = HistoricalCRUD()

    now = int(time.time())
    diff = now % chart_params["step"]
    right = now - diff
    left = right - (chart_params["limit"] * chart_params["step"])
    chart_params["start"] = left

    charts = await historical.get_charts(session=session, chart_params=chart_params, exchange_name=exchange_name)

    if currency != "USD":
        currency_rate = await get_fiat_currency_rate(session=session, currency=currency)
    else:
        currency_rate = 1
    print(charts)
    print(right, left)
    if not charts:
        return schema.ExchangeChartResponse(
            exchange_id=exchange_name,
            period=period,
            data=[]
        )
    step = chart_params["step"]
    chart_entries = []

    while left <= right:
        chart = charts.get(left)
        if not chart:
            chart = charts.get(left - step, {"volume_usd": 0})
            charts[left] = chart
        chart_entries.append(
            schema.ChartEntry(
                timestamp=left,
                volume=chart["volume_usd"] * currency_rate,
            )
        )
        left += step
    response = schema.ExchangeChartResponse(exchange_id=exchange_name,
                                            currency=currency,
                                            period=period,
                                            data=chart_entries)
    return response
