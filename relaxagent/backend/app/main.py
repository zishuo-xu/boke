from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.persistence.database import init_database
from app.presentation.api.error_handlers import register_exception_handlers
from app.presentation.api.v1.router import api_router
from app.shared.config import get_settings


settings = get_settings()

app = FastAPI(
    title="RelaxAgent Backend",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
init_database()


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")
