# Lab3
"""Create the sandbox and production databases if they do not exist.

The compose init script only runs on a fresh volume; this makes the two
environment databases on an already-initialised Postgres. Run from the root:

    python -m scripts.init_databases
"""

from __future__ import annotations

import asyncio

import asyncpg
from sqlalchemy.engine import make_url

from app.core.config import get_settings

_DATABASES = ("cyberimplant_sandbox", "cyberimplant_prod")


async def _create_all() -> None:
    url = make_url(get_settings().database_url)
    conn = await asyncpg.connect(
        host=url.host,
        port=url.port,
        user=url.username,
        password=url.password,
        database="postgres",
    )
    try:
        for name in _DATABASES:
            exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", name)
            if exists:
                print(f"database already exists: {name}")
            else:
                await conn.execute(f'CREATE DATABASE "{name}"')
                print(f"database created: {name}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(_create_all())
