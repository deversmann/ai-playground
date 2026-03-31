"""
Health check endpoint.

Provides a simple endpoint to check if the API is running and healthy.
Useful for:
1. Monitoring and alerting
2. Load balancer health checks
3. Development verification
4. CI/CD pipeline checks

Example:
    $ curl http://localhost:8000/health
    {"status": "healthy", "version": "0.4.0", "provider": "anthropic"}
"""

from fastapi import APIRouter, Depends

from chatbot.config import Settings
from ..dependencies import get_current_settings
from ..models import HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running and healthy",
    response_description="Health status and configuration info",
)
async def health_check(
    settings: Settings = Depends(get_current_settings),
) -> HealthResponse:
    """
    Health check endpoint.

    Returns basic information about the API status and configuration.
    This endpoint should always return 200 if the server is running.

    Args:
        settings: Application settings (injected)

    Returns:
        HealthResponse with status, version, and provider info

    Example:
        >>> # HTTP GET /health
        >>> {
        ...     "status": "healthy",
        ...     "version": "0.4.0",
        ...     "provider": "anthropic"
        ... }
    """
    return HealthResponse(
        status="healthy", version="0.4.0", provider=settings.provider_type
    )
