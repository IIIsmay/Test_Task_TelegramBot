import asyncpg
import logging
from typing import Optional

from app.config import Settings

logger = logging.getLogger(__name__)

_pool = None
_settings: Optional[Settings] = None


async def get_pool():
    global _pool, _settings
    if _settings is None:
        _settings = Settings()
    if _pool is None:
        logger.info("Creating PostgreSQL connection pool")
        _pool = await asyncpg.create_pool(_settings.database_url)
    return _pool


async def fetchval(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        logger.info("Executing SQL: %s | args=%s", query.strip(), args)
        return await conn.fetchval(query, *args)
