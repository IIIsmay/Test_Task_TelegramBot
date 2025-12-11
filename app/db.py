import asyncpg
from typing import Optional

from .config import Settings

_settings: Optional[Settings] = None
_pool: Optional[asyncpg.pool.Pool] = None


async def get_pool() -> asyncpg.pool.Pool:
    global _pool, _settings
    if _settings is None:
        _settings = Settings()
    if _pool is None:
        _pool = await asyncpg.create_pool(_settings.database_url, min_size=1, max_size=5)
    return _pool


async def fetchval(query: str, *args):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchval(query, *args)
