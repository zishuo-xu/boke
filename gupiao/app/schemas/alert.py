from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ========== 预警相关 Schema ==========

class AlertBase(BaseModel):
    """预警基础模型"""
    stock_id: int = Field(..., description="标的ID")
    alert_type: str = Field(..., description="预警类型：upper/lower")
    threshold: float = Field(..., description="预警阈值")


class AlertCreate(AlertBase):
    """创建预警模型"""
    pass


class AlertUpdate(BaseModel):
    """更新预警模型"""
    threshold: Optional[float] = Field(None, description="预警阈值")
    enabled: Optional[bool] = Field(None, description="是否启用")


class AlertResponse(AlertBase):
    """预警响应模型"""
    id: int
    user_id: int
    enabled: bool
    triggered_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertResponseWithStock(AlertResponse):
    """带标的信息的预警响应模型"""
    stock_code: str = Field(..., description="标的代码")
    stock_name: str = Field(..., description="标的名称")


# ========== 通知相关 Schema ==========

class NotificationResponse(BaseModel):
    """通知响应模型"""
    id: int
    user_id: int
    alert_id: int
    message: str
    is_read: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationWithAlert(NotificationResponse):
    """带预警信息的通知响应模型"""
    stock_code: str = Field(..., description="标的代码")
    stock_name: str = Field(..., description="标的名称")
    alert_type: str = Field(..., description="预警类型")
