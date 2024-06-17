from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.cruds.crud_historical import HistoricalCRUD
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
        "limit": 360,
        "type": "daily",
        "step": 86400,
    }
}


async def get_charts(exchange_name: str,
                     period: Literal['24h', '7d', '14d', '1M', '3M', '1Y'],
                     session: AsyncSession) -> schema.ExchangeChartResponse:
    """
        Get exchanges volumes chart
    """
    chart_params = CHART.get(period)
    historical = HistoricalCRUD()
    charts = await historical.get_charts(session=session, chart_params=chart_params, exchange_name=exchange_name)
    if not charts:
        return schema.ExchangeChartResponse(
            exchange_id=exchange_name,
            period=period,
            data=[]
        )
    right = max(charts.keys())
    left = right - (chart_params["limit"] * chart_params["step"])
    step = chart_params["step"]
    chart_entries = []
    while left <= right:
        if not charts.get(left):
            charts[left] = charts.get(left - step)
        chart_entries.append(
            schema.ChartEntry(
                timestamp=left,
                volume_usd=charts[left]["volume_usd"],
            )
        )
        left += step
    response = schema.ExchangeChartResponse(exchange_id=exchange_name,
                                            period=period,
                                            data=chart_entries)
    return response
