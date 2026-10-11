# Lab2
"""Seed (idempotently) an admin account.

Admins cannot self-register through the public API, so this bootstraps the first
operator account. Run from the project root:

    python -m scripts.seed_admin --email admin@example.com --password secret123
"""

from __future__ import annotations

import argparse
import asyncio

from app.db.session import async_session_factory
from app.models.user import UserRole
from app.services import user_service


async def _seed(email: str, password: str) -> None:
    async with async_session_factory() as session:
        existing = await user_service.get_by_email(session, email)
        if existing is not None:
            print(f"admin already exists: {email}")
            return
        await user_service.register_user(session, email, password, role=UserRole.ADMIN)
        print(f"admin created: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed an admin user.")
    parser.add_argument("--email", default="admin@cyberimplant.dev")
    parser.add_argument("--password", default="admin-password-123")
    args = parser.parse_args()
    asyncio.run(_seed(args.email, args.password))


if __name__ == "__main__":
    main()
