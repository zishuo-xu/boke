import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用基本信息
    APP_NAME: str = "股票/基金数据监控面板"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/finance.db"

    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天

    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:8000", "http://localhost:3000"]

    # Claude API配置（预留）
    CLAUDE_API_KEY: str = ""

    # 邮件配置（可选）
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    # 缓存配置
    STOCK_CACHE_TTL: int = 300  # 股票数据缓存5分钟
    FUND_CACHE_TTL: int = 600   # 基金数据缓存10分钟
    HISTORY_CACHE_TTL: int = 3600  # 历史数据缓存1小时

    # 数据刷新频率（秒）
    STOCK_REFRESH_INTERVAL: int = 300  # 5分钟
    FUND_REFRESH_INTERVAL: int = 600   # 10分钟
    ALERT_CHECK_INTERVAL: int = 60     # 1分钟

    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()
