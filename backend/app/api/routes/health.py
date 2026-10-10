from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends

from app.config import settings
from app.database.mongodb import MongoDBManager
from app.dependencies import get_db

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Service health check")
async def health_check(db: MongoDBManager = Depends(get_db)) -> Dict[str, Any]:
    """
    Check the health of the backend application and its dependencies.
    Distinguishes application responsiveness from external database connectivity.
    """
    db_alive = await db.ping()
    overall_status = "healthy" if db_alive else "degraded"

    return {
        "status": overall_status,
        "database": "connected" if db_alive else "disconnected",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": "ok",
            "database": "ok" if db_alive else "unavailable",
            "tavily_configured": bool(settings.TAVILY_API_KEY and not settings.TAVILY_API_KEY.startswith("tvly-your_")),
            "groq_configured": bool(settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_your_")),
        },
    }
