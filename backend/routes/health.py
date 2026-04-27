"""
routes/health.py
Simple health and readiness check endpoint.
"""

from fastapi import APIRouter
from models.schemas import HealthResponse
from services.model_service import ModelService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Returns service health and whether the ML model is loaded."""
    model = ModelService.get_instance()
    return HealthResponse(
        status="ok",
        model_loaded=model.is_loaded,
    )
