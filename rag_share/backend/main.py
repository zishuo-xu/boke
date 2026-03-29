from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from routers import rag

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

app = FastAPI(title="RAG Visualization API")

cors_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
)
allow_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(rag.router, prefix="/api", tags=["RAG"])


@app.get("/")
async def root():
    return {"message": "RAG Visualization API", "docs": "/docs"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
