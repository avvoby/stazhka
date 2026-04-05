from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_telegram_id", "telegram_id", unique=True),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str] = mapped_column(String(64), default="")
    first_name: Mapped[str] = mapped_column(String(128), default="")
    last_name: Mapped[str] = mapped_column(String(128), default="")
    language_code: Mapped[str] = mapped_column(String(8), default="ru")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    profile: Mapped["UserProfileModel | None"] = relationship(
        "UserProfileModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    applications: Mapped[list["ApplicationModel"]] = relationship(
        "ApplicationModel",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserProfileModel(Base):
    __tablename__ = "user_profiles"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(String(256), default="")
    university: Mapped[str] = mapped_column(String(256), default="")
    specialty: Mapped[str] = mapped_column(String(256), default="")
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    desired_position: Mapped[str] = mapped_column(String(256), default="")
    desired_city: Mapped[str] = mapped_column(String(128), default="")
    resume_url: Mapped[str] = mapped_column(String(512), default="")
    about: Mapped[str] = mapped_column(Text, default="")
    search_status: Mapped[str] = mapped_column(String(32), default="active")
    # v2 расширенные поля
    gpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    language: Mapped[str | None] = mapped_column(String(64), nullable=True)
    experience: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_salary: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="profile"
    )


class VacancyModel(Base):
    __tablename__ = "vacancies"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    title: Mapped[str] = mapped_column(String(256), default="")
    company: Mapped[str] = mapped_column(String(256), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    requirements: Mapped[str] = mapped_column(Text, default="")
    city: Mapped[str] = mapped_column(String(128), default="")
    work_format: Mapped[str] = mapped_column(String(32), default="unspecified")
    salary_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(8), default="RUB")
    source: Mapped[str] = mapped_column(String(32), default="manual")
    source_url: Mapped[str] = mapped_column(String(512), default="")
    source_id: Mapped[str] = mapped_column(String(256), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    applications: Mapped[list["ApplicationModel"]] = relationship(
        "ApplicationModel",
        back_populates="vacancy",
        cascade="all, delete-orphan",
    )


class ApplicationModel(Base):
    __tablename__ = "applications"
    __table_args__ = (
        Index("ix_applications_user_id", "user_id"),
    )

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    vacancy_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage: Mapped[str] = mapped_column(String(32), default="saved")
    notes: Mapped[str] = mapped_column(Text, default="")
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    next_step: Mapped[str] = mapped_column(String(512), default="")
    next_step_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="applications"
    )
    vacancy: Mapped["VacancyModel"] = relationship(
        "VacancyModel", back_populates="applications"
    )
