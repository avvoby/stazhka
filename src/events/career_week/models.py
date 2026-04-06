from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


@dataclass
class CareerWeekRegistration:
    id: UUID
    user_id: UUID
    code: str              # 5-значный числовой код, например "47823"
    direction: str         # направление обучения
    program: str           # программа обучения
    course: str            # курс
    skills: list[str]
    registered_at: datetime


@dataclass
class RoastSlot:
    id: str
    type: str              # "resume" | "interview"
    date: str
    time: str
    direction: str         # Консалтинг / Бигтех / Финансы и т.д.
    capacity: int
    registrations_count: int

    @property
    def is_available(self) -> bool:
        return self.registrations_count < self.capacity

    @property
    def available_seats(self) -> int:
        return self.capacity - self.registrations_count


@dataclass
class RoastBooking:
    id: UUID
    user_id: UUID
    slot_id: str
    slot_type: str
    direction: str
    resume_file_id: str | None    # Telegram file_id
    resume_url: str | None        # ссылка на Google Drive / HH
    booked_at: datetime
    cancelled_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.cancelled_at is None


@dataclass
class Partner:
    name: str
    description: str
    logo_url: str
    roast_direction: str
    day: str
    time: str


@dataclass
class ScheduleEvent:
    day: str
    date: str
    time_start: str
    time_end: str
    title: str
    location: str
    description: str
