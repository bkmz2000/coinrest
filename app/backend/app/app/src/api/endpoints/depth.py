from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from src.db import connection
from src.api.rest.depth import get_depth
from src.lib.schema import MarketDepthResponse

router = APIRouter()


@router.get("/", response_model=MarketDepthResponse | None)
async def get_market_depth(cg_id: str,
                           depth: int = Query(2, description="market depth in percents"),
                           session: AsyncSession = Depends(connection.get_db)):
    """
        Get market depth
    """
    return await get_depth(cg_id=cg_id, depth=depth, session=session)


