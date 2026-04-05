from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.domain.value_objects.application_stage import ApplicationStage


@dataclass
class Application:
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default=None)  # type: ignore[assignment]
    vacancy_id: UUID = field(default=None)  # type: ignore[assignment]
    stage: ApplicationStage = ApplicationStage.SAVED
    notes: str = ""
    applied_at: datetime | None = None
    next_step: str = ""
    next_step_date: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    # Денормализованные поля из Vacancy — заполняются при joinedload
    vacancy_title: str = ""
    vacancy_company: str = ""
    vacancy_url: str = ""

    def advance_to(self, stage: ApplicationStage) -> None:
        """Перевести отклик на следующий этап."""
        self.stage = stage
        self.updated_at = datetime.utcnow()
        if stage == ApplicationStage.APPLIED and self.applied_at is None:
            self.applied_at = datetime.utcnow()

    @property
    def is_active(self) -> bool:
        return self.stage not in (
            ApplicationStage.OFFER,
            ApplicationStage.REJECTED,
        )
