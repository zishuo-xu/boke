from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ========== 标的相关 Schema ==========

class StockBase(BaseModel):
    """标的基础模型"""
    code: str = Field(..., description="标的代码")
    name: str = Field(..., description="标的名称")
    type: str = Field(..., description="标的类型：stock/fund")


class StockCreate(StockBase):
    """创建标的模型"""
    group_id: Optional[int] = Field(None, description="分组ID")


class StockUpdate(BaseModel):
    """更新标的模型"""
    name: Optional[str] = None
    group_id: Optional[int] = None
    sort_order: Optional[int] = None


class StockResponse(StockBase):
    """标的响应模型"""
    id: int
    user_id: int
    market: Optional[str] = None
    sector: Optional[str] = None
    fund_company: Optional[str] = None
    fund_type: Optional[str] = None
    group_id: Optional[int] = None
    sort_order: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockSearch(BaseModel):
    """搜索标的模型"""
    keyword: str = Field(..., description="搜索关键词（代码或名称）")
    type: Optional[str] = Field(None, description="标的类型筛选：stock/fund")


# ========== 分组相关 Schema ==========

class GroupBase(BaseModel):
    """分组基础模型"""
    name: str = Field(..., min_length=1, max_length=50, description="分组名称")


class GroupCreate(GroupBase):
    """创建分组模型"""
    sort_order: Optional[int] = Field(0, description="排序顺序")


class GroupUpdate(BaseModel):
    """更新分组模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    sort_order: Optional[int] = None


class GroupResponse(GroupBase):
    """分组响应模型"""
    id: int
    user_id: int
    sort_order: int
    stock_count: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
