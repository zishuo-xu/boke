from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.market import (
    StockRealtimeData, FundRealtimeData,
    StockHistoryData, FundHistoryData,
    BatchStocksData, DataRefreshRequest
)
from app.services.market_service import market_service

router = APIRouter()


# ========== 股票代码查询 API ==========
@router.get("/stock/code/{stock_code}", response_model=StockRealtimeData)
def get_stock_by_code(
    stock_code: str,
    force: bool = Query(False, description="是否强制刷新"),
):
    """
    根据股票代码获取实时数据（无需登录）

    - **stock_code**: 股票代码（如 600036）
    - **force**: 是否强制刷新
    """
    data = market_service.get_stock_by_code(stock_code, force)

    if not data:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="股票数据获取失败"
        )

    return data


# ========== 股票数据 API ==========

@router.get("/stock/{stock_id}", response_model=StockRealtimeData)
def get_stock_realtime(
    stock_id: int,
    force: bool = Query(False, description="是否强制刷新"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取股票实时数据

    - **stock_id**: 股票ID
    - **force**: 是否强制刷新（忽略缓存）
    """
    data = market_service.get_stock_realtime(db, current_user.id, stock_id, force)

    if not data:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="股票数据获取失败"
        )

    return data


@router.get("/stock/{stock_id}/history", response_model=List[StockHistoryData])
def get_stock_history(
    stock_id: int,
    period: str = Query("30d", description="时间周期：7d/30d/90d/1y"),
    force: bool = Query(False, description="是否强制刷新"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取股票历史数据

    - **stock_id**: 股票ID
    - **period**: 时间周期
    - **force**: 是否强制刷新
    """
    data = market_service.get_stock_history(db, current_user.id, stock_id, period, force)

    if not data:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="股票历史数据获取失败"
        )

    return data


# ========== 基金数据 API ==========

@router.get("/fund/{stock_id}", response_model=FundRealtimeData)
def get_fund_realtime(
    stock_id: int,
    force: bool = Query(False, description="是否强制刷新"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取基金实时数据

    - **stock_id**: 基金ID
    - **force**: 是否强制刷新
    """
    data = market_service.get_fund_realtime(db, current_user.id, stock_id, force)

    if not data:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="基金数据获取失败"
        )

    return data


@router.get("/fund/{stock_id}/history", response_model=List[FundHistoryData])
def get_fund_history(
    stock_id: int,
    period: str = Query("30d", description="时间周期：7d/30d/90d/1y"),
    force: bool = Query(False, description="是否强制刷新"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取基金历史数据

    - **stock_id**: 基金ID
    - **period**: 时间周期
    - **force**: 是否强制刷新
    """
    data = market_service.get_fund_history(db, current_user.id, stock_id, period, force)

    if not data:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="基金历史数据获取失败"
        )

    return data


# ========== 批量数据 API ==========

@router.post("/batch", response_model=BatchStocksData)
def get_batch_stocks_realtime(
    request: DataRefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量获取股票实时数据

    - **stock_ids**: 股票ID列表
    - **force**: 是否强制刷新
    """
    if not request.stock_ids:
        return BatchStocksData(stocks=[])

    data = market_service.get_batch_stocks_realtime(
        db,
        current_user.id,
        request.stock_ids,
        request.force
    )

    return BatchStocksData(stocks=list(data.values()))


# ========== 数据刷新 API ==========

@router.post("/refresh")
def refresh_all_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    刷新所有数据

    刷新用户的所有股票和基金数据
    """
    stock_count = market_service.refresh_all_stocks(db, current_user.id)
    fund_count = market_service.refresh_all_funds(db, current_user.id)

    return {
        "message": "数据刷新完成",
        "stock_count": stock_count,
        "fund_count": fund_count,
        "total": stock_count + fund_count
    }
