from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter()


class AIAnalysisRequest(BaseModel):
    """AI解读请求模型"""
    stock_id: int
    style: Optional[str] = "simple"  # simple, concise, professional


class AIAnalysisResponse(BaseModel):
    """AI解读响应模型"""
    content: str
    style: str
    stock_name: str


@router.post("/stock", response_model=AIAnalysisResponse)
def analyze_stock(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    股票AI解读（功能开发中）

    - **stock_id**: 股票ID
    - **style**: 解读风格（simple/concise/professional）
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI解读功能开发中，敬请期待"
    )


@router.post("/fund", response_model=AIAnalysisResponse)
def analyze_fund(
    request: AIAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    基金AI解读（功能开发中）

    - **stock_id**: 基金ID
    - **style**: 解读风格（simple/concise/professional）
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI解读功能开发中，敬请期待"
    )


class PortfolioAnalysisRequest(BaseModel):
    """组合AI解读请求模型"""
    group_id: int
    style: Optional[str] = "simple"


class PortfolioAnalysisResponse(BaseModel):
    """组合AI解读响应模型"""
    content: str
    style: str
    group_name: str


@router.post("/portfolio", response_model=PortfolioAnalysisResponse)
def analyze_portfolio(
    request: PortfolioAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """
    组合AI解读（功能开发中）

    - **group_id**: 分组ID
    - **style**: 解读风格（simple/concise/professional）
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI解读功能开发中，敬请期待"
    )
