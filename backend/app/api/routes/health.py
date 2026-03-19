"""Health-check route."""
from fastapi import APIRouter

from backend.app.models.response import HealthResponse
from backend.utils.db import ping_mongo

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    """Return application and MongoDB health status."""
    mongo_ok = ping_mongo()
    return HealthResponse(
        status="ok" if mongo_ok else "degraded",
        mongo="up" if mongo_ok else "down",
    )
