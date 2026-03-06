from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.watchlist import (
    StockCreate, StockUpdate, StockResponse, StockSearch,
    GroupCreate, GroupUpdate, GroupResponse
)
from app.services.watchlist_service import WatchlistService, GroupService

router = APIRouter()


# ========== 标的管理 API ==========

@router.post("", response_model=StockResponse, status_code=status.HTTP_201_CREATED)
def add_stock(
    stock_data: StockCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    添加自选标的

    - **code**: 标的代码（股票：6位数字；港股：5位数字.HK；美股：字母；基金：6位数字）
    - **name**: 标的名称
    - **type**: 标的类型（stock/fund）
    - **group_id**: 分组ID（可选，不填则加入未分组）
    """
    try:
        stock = WatchlistService.add_stock(db, current_user.id, stock_data)
        return stock
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[StockResponse])
def get_watchlist(
    group_id: Optional[int] = Query(None, description="分组ID筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取自选列表

    - **group_id**: 可选，指定分组ID筛选
    """
    stocks = WatchlistService.get_stocks(db, current_user.id, group_id)
    return stocks


@router.get("/{stock_id}", response_model=StockResponse)
def get_stock(
    stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个标的详情
    """
    stock = WatchlistService.get_stock_by_id(db, current_user.id, stock_id)

    if not stock:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标的不存在"
        )

    return stock


@router.put("/{stock_id}", response_model=StockResponse)
def update_stock(
    stock_id: int,
    stock_data: StockUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新标的信息

    - **name**: 标的名称（可选）
    - **group_id**: 分组ID（可选，设为0移动到未分组）
    - **sort_order**: 排序顺序（可选）
    """
    try:
        stock = WatchlistService.update_stock(db, current_user.id, stock_id, stock_data)
        return stock
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{stock_id}")
def delete_stock(
    stock_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除标的
    """
    try:
        WatchlistService.delete_stock(db, current_user.id, stock_id)
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/search", response_model=List[StockResponse])
def search_stocks(
    search_data: StockSearch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    模糊搜索标的

    - **keyword**: 搜索关键词（代码或名称）
    - **type**: 标的类型筛选（可选：stock/fund）
    """
    stocks = WatchlistService.search_stocks(
        db,
        current_user.id,
        search_data.keyword,
        search_data.type
    )
    return stocks


# ========== 分组管理 API ==========

@router.post("/groups", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    group_data: GroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建分组

    - **name**: 分组名称
    - **sort_order**: 排序顺序（可选）
    """
    try:
        group = GroupService.create_group(db, current_user.id, group_data)
        return group
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/groups", response_model=List[GroupResponse])
def get_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取分组列表

    返回所有分组，每个分组包含标的数量
    """
    groups = GroupService.get_groups(db, current_user.id)
    return groups


@router.get("/groups/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取单个分组详情
    """
    group = GroupService.get_group_by_id(db, current_user.id, group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )

    # 添加标的数量
    from app.models.stock import Stock
    group.stock_count = db.query(Stock).filter(Stock.group_id == group_id).count()

    return group


@router.put("/groups/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    group_data: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新分组

    - **name**: 分组名称（可选）
    - **sort_order**: 排序顺序（可选）
    """
    try:
        group = GroupService.update_group(db, current_user.id, group_id, group_data)
        return group
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除分组

    删除分组后，该分组下的标的将自动移动到未分组
    """
    try:
        GroupService.delete_group(db, current_user.id, group_id)
        return {"message": "删除成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
