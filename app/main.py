from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import vaccines

app = FastAPI(
    title="Averlyn Vaccine Tracker API",
    version="1.0.0",
)

# CORS — only allow the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers
app.include_router(vaccines.router)


@app.get("/health")
async def health_check():
    """Health check endpoint (no auth required)."""
    return {"status": "ok"}
