from typing import Protocol
from uuid import UUID

from src.domain.entities.vacancy import Vacancy
from src.domain.value_objects.vacancy_source import VacancySource
from src.domain.value_objects.work_format import WorkFormat


class VacancyRepository(Protocol):
    async def get_by_id(self, vacancy_id: UUID) -> Vacancy | None: ...

    async def get_by_source_id(
        self, source: VacancySource, source_id: str
    ) -> Vacancy | None: ...

    async def create(self, vacancy: Vacancy) -> Vacancy: ...

    async def update(self, vacancy: Vacancy) -> Vacancy: ...

    async def delete(self, vacancy_id: UUID) -> None: ...

    async def search(
        self,
        query: str = "",
        city: str = "",
        work_format: WorkFormat | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Vacancy]: ...

    async def get_all_active(
        self, limit: int = 20, offset: int = 0
    ) -> list[Vacancy]: ...
