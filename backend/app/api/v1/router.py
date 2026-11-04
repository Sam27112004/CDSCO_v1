from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.evidence import router as evidence_router
from app.api.v1.submissions import router as submissions_router
from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthResponse

api_router = APIRouter()

# Mount feature routers
api_router.include_router(submissions_router)
api_router.include_router(evidence_router)


@api_router.get("/health", response_model=HealthResponse, tags=["Health"])
async def check_health(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Verifies service readiness and database connectivity."""
    db_connected = False
    try:
        result = await db.execute(text("SELECT 1"))
        db_connected = result.scalar() == 1
    except Exception:
        db_connected = False

    return HealthResponse(
        status="healthy" if db_connected else "degraded",
        version=settings.VERSION,
        project_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        database_connected=db_connected,
    )
