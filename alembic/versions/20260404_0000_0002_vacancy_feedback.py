"""vacancy_feedback

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-04 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vacancy_feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vacancy_id", postgresql.UUID(as_uuid=True), nullable=True),
        # source_id + source для вакансий без vacancy_id (из агрегатора, не сохранённых в БД)
        sa.Column("source_id", sa.String(128), nullable=False, server_default=""),
        sa.Column("source", sa.String(32), nullable=False, server_default="hh"),
        sa.Column(
            "feedback",
            sa.String(16),
            nullable=False,
            comment="like | dislike | apply | ignore",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vacancy_id"], ["vacancies.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_vacancy_feedback_user_id", "vacancy_feedback", ["user_id"])
    op.create_index(
        "ix_vacancy_feedback_user_source",
        "vacancy_feedback",
        ["user_id", "source_id", "source"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_vacancy_feedback_user_source", table_name="vacancy_feedback")
    op.drop_index("ix_vacancy_feedback_user_id", table_name="vacancy_feedback")
    op.drop_table("vacancy_feedback")
