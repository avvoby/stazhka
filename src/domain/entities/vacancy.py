from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.value_objects.vacancy_source import VacancySource
from src.domain.value_objects.work_format import WorkFormat


@dataclass
class Vacancy:
    id: UUID = field(default_factory=uuid4)
    title: str = ""
    company: str = ""
    description: str = ""
    requirements: str = ""
    city: str = ""
    work_format: WorkFormat = WorkFormat.UNSPECIFIED
    salary_from: int | None = None
    salary_to: int | None = None
    salary_currency: str = "RUB"
    source: VacancySource = VacancySource.MANUAL
    source_url: str = ""
    source_id: str = ""
    is_active: bool = True
    published_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def salary_display(self) -> str:
        if self.salary_from and self.salary_to:
            return f"{self.salary_from:,}–{self.salary_to:,} {self.salary_currency}"
        if self.salary_from:
            return f"от {self.salary_from:,} {self.salary_currency}"
        if self.salary_to:
            return f"до {self.salary_to:,} {self.salary_currency}"
        return "не указана"

    @property
    def short_description(self) -> str:
        if len(self.description) <= 300:
            return self.description
        return self.description[:297] + "..."
