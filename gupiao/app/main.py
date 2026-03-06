from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    yield
    # 关闭时的清理工作


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="股票/基金数据监控+AI解读面板",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（使用绝对路径）
import os
from pathlib import Path

static_dir = Path(__file__).parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


from fastapi.responses import HTMLResponse, Response


@app.get("/")
async def root():
    """根路径 - 返回前端页面"""
    from pathlib import Path
    index_path = Path(__file__).parent.parent / "frontend" / "index.html"
    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="text/html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@app.get("/app")
async def app_page():
    """主应用页面"""
    from pathlib import Path
    app_path = Path(__file__).parent.parent / "frontend" / "app.html"
    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()
    return Response(
        content=content,
        media_type="text/html",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
    )


@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


# 注册API路由
from app.api.v1 import user, watchlist, market, alert, ai_analysis

app.include_router(user.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(watchlist.router, prefix="/api/v1/watchlist", tags=["自选管理"])
app.include_router(market.router, prefix="/api/v1/market", tags=["数据监控"])
app.include_router(alert.router, prefix="/api/v1/alerts", tags=["预警"])
app.include_router(ai_analysis.router, prefix="/api/v1/ai", tags=["AI解读"])
