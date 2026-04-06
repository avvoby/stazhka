"""career_week tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-04 00:02:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── career_week_registrations ─────────────────────────────────────────────
    op.create_table(
        "career_week_registrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(5), nullable=False),
        sa.Column("direction", sa.String(100), nullable=False, server_default=""),
        sa.Column("program", sa.String(100), nullable=False, server_default=""),
        sa.Column("course", sa.String(20), nullable=False, server_default=""),
        sa.Column("skills", postgresql.JSON(), nullable=False, server_default="[]"),
        sa.Column(
            "registered_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_career_week_registrations_code"),
        sa.UniqueConstraint("user_id", name="uq_career_week_registrations_user_id"),
    )
    op.create_index(
        "ix_career_week_registrations_user_id",
        "career_week_registrations",
        ["user_id"],
    )

    # ── career_week_roast_bookings ────────────────────────────────────────────
    op.create_table(
        "career_week_roast_bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("slot_id", sa.String(50), nullable=False),
        sa.Column("slot_type", sa.String(20), nullable=False),
        sa.Column("direction", sa.String(100), nullable=False, server_default=""),
        sa.Column("resume_file_id", sa.String(255), nullable=True),
        sa.Column("resume_url", sa.String(500), nullable=True),
        sa.Column(
            "booked_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_career_week_roast_bookings_user_id",
        "career_week_roast_bookings",
        ["user_id"],
    )

    # ── career_week_slots_cache ───────────────────────────────────────────────
    op.create_table(
        "career_week_slots_cache",
        sa.Column("slot_id", sa.String(50), nullable=False),
        sa.Column("registrations_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("slot_id"),
    )


def downgrade() -> None:
    op.drop_table("career_week_slots_cache")
    op.drop_index("ix_career_week_roast_bookings_user_id", table_name="career_week_roast_bookings")
    op.drop_table("career_week_roast_bookings")
    op.drop_index("ix_career_week_registrations_user_id", table_name="career_week_registrations")
    op.drop_table("career_week_registrations")
