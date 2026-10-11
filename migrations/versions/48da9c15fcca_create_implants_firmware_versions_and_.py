"""create implants firmware_versions and ota_update_jobs tables

Revision ID: 48da9c15fcca
Revises:
Create Date: 2026-09-13 19:03:19.391590

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "48da9c15fcca"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "implants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("serial_number", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("current_firmware_version", sa.String(length=32), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "OFFLINE", "QUARANTINED", name="implant_status"),
            nullable=False,
        ),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_implants_serial_number", "implants", ["serial_number"], unique=True)

    op.create_table(
        "firmware_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("artifact_url", sa.String(length=512), nullable=False),
        sa.Column("release_notes", sa.String(length=2048), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_firmware_versions_version", "firmware_versions", ["version"], unique=True)

    op.create_table(
        "ota_update_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "implant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("implants.id"),
            nullable=False,
        ),
        sa.Column(
            "firmware_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("firmware_versions.id"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "IN_PROGRESS", "SUCCEEDED", "FAILED", name="ota_job_status"),
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ota_update_jobs_implant_id", "ota_update_jobs", ["implant_id"])
    op.create_index(
        "ix_ota_update_jobs_firmware_version_id", "ota_update_jobs", ["firmware_version_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("ota_update_jobs")
    op.drop_table("firmware_versions")
    op.drop_table("implants")
    op.execute("DROP TYPE IF EXISTS ota_job_status")
    op.execute("DROP TYPE IF EXISTS implant_status")
