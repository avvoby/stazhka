"""extend_user_profile

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-04 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("gpa", sa.Float(), nullable=True))
    op.add_column("user_profiles", sa.Column("language", sa.String(64), nullable=True))
    op.add_column("user_profiles", sa.Column("experience", sa.Text(), nullable=True))
    op.add_column("user_profiles", sa.Column("expected_salary", sa.Integer(), nullable=True))
    op.add_column(
        "user_profiles",
        sa.Column("notifications_enabled", sa.Boolean(), nullable=False, server_default="true"),
    )


def downgrade() -> None:
    op.drop_column("user_profiles", "notifications_enabled")
    op.drop_column("user_profiles", "expected_salary")
    op.drop_column("user_profiles", "experience")
    op.drop_column("user_profiles", "language")
    op.drop_column("user_profiles", "gpa")
