from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.value_objects.search_status import SearchStatus


@dataclass
class UserProfile:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)  # type: ignore[assignment]
    full_name: str = ""
    university: str = ""
    specialty: str = ""
    graduation_year: int | None = None
    skills: list[str] = field(default_factory=list)
    desired_position: str = ""
    desired_city: str = ""
    resume_url: str = ""
    about: str = ""
    search_status: SearchStatus = SearchStatus.ACTIVE
    # v2 расширенные поля
    gpa: float | None = None
    language: str | None = None
    experience: str | None = None
    expected_salary: int | None = None
    notifications_enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def is_complete(self) -> bool:
        """Профиль заполнен достаточно для поиска стажировок."""
        return bool(self.specialty and self.skills)


@dataclass
class User:
    id: UUID = field(default_factory=uuid4)
    telegram_id: int = 0
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    language_code: str = "ru"
    is_active: bool = True
    is_blocked: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    profile: UserProfile | None = None

    @property
    def display_name(self) -> str:
        if self.first_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.username or str(self.telegram_id)
