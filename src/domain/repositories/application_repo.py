from typing import Protocol
from uuid import UUID

from src.domain.entities.application import Application
from src.domain.value_objects.application_stage import ApplicationStage


class ApplicationRepository(Protocol):
    async def get_by_id(self, application_id: UUID) -> Application | None: ...

    async def get_by_user(
        self,
        user_id: UUID,
        stage: ApplicationStage | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Application]: ...

    async def get_by_user_and_vacancy(
        self, user_id: UUID, vacancy_id: UUID
    ) -> Application | None: ...

    async def create(self, application: Application) -> Application: ...

    async def update(self, application: Application) -> Application: ...

    async def delete(self, application_id: UUID) -> None: ...

    async def count_by_user(self, user_id: UUID) -> int: ...
