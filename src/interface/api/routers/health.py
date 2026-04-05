import logging

import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from src.core.config import settings
from src.infrastructure.database.connection import AsyncSessionFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    result: dict[str, str] = {"status": "ok"}

    # PostgreSQL
    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        result["db"] = "ok"
    except Exception as e:
        logger.error("DB health check failed: %s", e)
        result["db"] = "error"
        result["status"] = "degraded"

    # Redis
    try:
        r = aioredis.from_url(settings.redis.url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        result["redis"] = "ok"
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        result["redis"] = "error"
        result["status"] = "degraded"

    return result
