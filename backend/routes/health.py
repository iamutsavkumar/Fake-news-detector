"""
routes/health.py
Simple health and readiness check endpoint.
"""

from fastapi import APIRouter
from models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns service health status."""
    return HealthResponse(
        status="ok",
        model_loaded=False,
    )