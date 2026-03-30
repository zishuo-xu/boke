from fastapi import APIRouter

from app.presentation.api.v1.routes.agents import router as agents_router
from app.presentation.api.v1.routes.chat import router as chat_router
from app.presentation.api.v1.routes.providers import router as providers_router
from app.presentation.api.v1.routes.sessions import router as sessions_router


api_router = APIRouter()
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(providers_router, prefix="/providers", tags=["providers"])
api_router.include_router(sessions_router, prefix="/sessions", tags=["sessions"])
