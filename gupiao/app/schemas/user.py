from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr
    nickname: Optional[str] = None


class UserCreate(UserBase):
    """用户注册模型"""
    password: str = Field(..., min_length=6, max_length=18, description="密码长度6-18字符")


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token数据模型"""
    user_id: Optional[int] = None
