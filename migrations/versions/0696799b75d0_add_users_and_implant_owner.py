"""add users and implant owner

Revision ID: 0696799b75d0
Revises: 48da9c15fcca
Create Date: 2026-10-11 14:16:20.454692

"""

# Lab2
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0696799b75d0"
down_revision: str | Sequence[str] | None = "48da9c15fcca"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OWNER_FK = "fk_implants_owner_id_users"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=256), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "USER", name="user_role"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column("implants", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_implants_owner_id", "implants", ["owner_id"])
    op.create_foreign_key(_OWNER_FK, "implants", "users", ["owner_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_OWNER_FK, "implants", type_="foreignkey")
    op.drop_index("ix_implants_owner_id", table_name="implants")
    op.drop_column("implants", "owner_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role")
