"""initial

Revision ID: 0001
Revises:
Create Date: 2026-03-22 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64), nullable=False, server_default=""),
        sa.Column("first_name", sa.String(128), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(128), nullable=False, server_default=""),
        sa.Column("language_code", sa.String(8), nullable=False, server_default="ru"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_blocked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=True)

    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("full_name", sa.String(256), nullable=False, server_default=""),
        sa.Column("university", sa.String(256), nullable=False, server_default=""),
        sa.Column("specialty", sa.String(256), nullable=False, server_default=""),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("skills", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("desired_position", sa.String(256), nullable=False, server_default=""),
        sa.Column("desired_city", sa.String(128), nullable=False, server_default=""),
        sa.Column("resume_url", sa.String(512), nullable=False, server_default=""),
        sa.Column("about", sa.Text(), nullable=False, server_default=""),
        sa.Column("search_status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "vacancies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(256), nullable=False, server_default=""),
        sa.Column("company", sa.String(256), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("requirements", sa.Text(), nullable=False, server_default=""),
        sa.Column("city", sa.String(128), nullable=False, server_default=""),
        sa.Column("work_format", sa.String(32), nullable=False, server_default="unspecified"),
        sa.Column("salary_from", sa.Integer(), nullable=True),
        sa.Column("salary_to", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(8), nullable=False, server_default="RUB"),
        sa.Column("source", sa.String(32), nullable=False, server_default="manual"),
        sa.Column("source_url", sa.String(512), nullable=False, server_default=""),
        sa.Column("source_id", sa.String(256), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "applications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False, server_default="saved"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("applied_at", sa.DateTime(), nullable=True),
        sa.Column("next_step", sa.String(512), nullable=False, server_default=""),
        sa.Column("next_step_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_applications_user_id", table_name="applications")
    op.drop_table("applications")
    op.drop_table("vacancies")
    op.drop_table("user_profiles")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")
