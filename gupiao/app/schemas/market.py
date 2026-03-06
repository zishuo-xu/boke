from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 股票数据 Schema ==========

class StockRealtimeData(BaseModel):
    """股票实时数据"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    price: float = Field(..., description="现价")
    change: float = Field(0, description="涨跌额")
    change_pct: float = Field(0, description="涨跌幅（%）")
    volume: float = Field(0, description="成交量")
    turnover_rate: Optional[float] = Field(None, description="换手率（%）")
    open: Optional[float] = Field(None, description="开盘价")
    close: Optional[float] = Field(None, description="昨收价")
    high: Optional[float] = Field(None, description="最高价")
    low: Optional[float] = Field(None, description="最低价")
    timestamp: Optional[datetime] = Field(None, description="数据时间戳")


class StockHistoryData(BaseModel):
    """股票历史数据"""
    date: str = Field(..., description="日期")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    change_pct: Optional[float] = Field(None, description="涨跌幅（%）")


# ========== 基金数据 Schema ==========

class FundRealtimeData(BaseModel):
    """基金实时数据"""
    code: str = Field(..., description="基金代码")
    name: str = Field(..., description="基金名称")
    nav: float = Field(..., description="单位净值")
    acc_nav: Optional[float] = Field(None, description="累计净值")
    est_nav: Optional[float] = Field(None, description="估算净值")
    change_pct: float = Field(0, description="涨跌幅（%）")
    day_nav: Optional[float] = Field(None, description="日涨幅（%）")
    timestamp: Optional[datetime] = Field(None, description="数据时间戳")


class FundHistoryData(BaseModel):
    """基金历史数据"""
    date: str = Field(..., description="日期")
    nav: float = Field(..., description="单位净值")
    acc_nav: Optional[float] = Field(None, description="累计净值")
    change_pct: Optional[float] = Field(None, description="涨跌幅（%）")


# ========== 批量数据 Schema ==========

class BatchStocksData(BaseModel):
    """批量股票数据"""
    stocks: List[StockRealtimeData] = Field(default_factory=list, description="股票列表")


# ========== 数据刷新请求 Schema ==========

class DataRefreshRequest(BaseModel):
    """数据刷新请求"""
    stock_ids: Optional[List[int]] = Field(None, description="股票ID列表")
    fund_ids: Optional[List[int]] = Field(None, description="基金ID列表")
    force: bool = Field(False, description="是否强制刷新")
