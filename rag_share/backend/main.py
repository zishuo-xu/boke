from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import rag

app = FastAPI(title="RAG Visualization API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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
