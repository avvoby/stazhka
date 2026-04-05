from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.vacancy import Vacancy
from src.domain.value_objects.vacancy_source import VacancySource
from src.domain.value_objects.work_format import WorkFormat
from src.infrastructure.database.models import VacancyModel


class VacancyRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Mappers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(model: VacancyModel) -> Vacancy:
        return Vacancy(
            id=model.id,
            title=model.title,
            company=model.company,
            description=model.description,
            requirements=model.requirements,
            city=model.city,
            work_format=WorkFormat(model.work_format),
            salary_from=model.salary_from,
            salary_to=model.salary_to,
            salary_currency=model.salary_currency,
            source=VacancySource(model.source),
            source_url=model.source_url,
            source_id=model.source_id,
            is_active=model.is_active,
            published_at=model.published_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(vacancy: Vacancy) -> VacancyModel:
        return VacancyModel(
            id=vacancy.id,
            title=vacancy.title,
            company=vacancy.company,
            description=vacancy.description,
            requirements=vacancy.requirements,
            city=vacancy.city,
            work_format=str(vacancy.work_format),
            salary_from=vacancy.salary_from,
            salary_to=vacancy.salary_to,
            salary_currency=vacancy.salary_currency,
            source=str(vacancy.source),
            source_url=vacancy.source_url,
            source_id=vacancy.source_id,
            is_active=vacancy.is_active,
            published_at=vacancy.published_at,
            created_at=vacancy.created_at,
            updated_at=vacancy.updated_at,
        )

    # ── Queries ──────────────────────────────────────────────────────────────

    async def get_by_id(self, vacancy_id: UUID) -> Vacancy | None:
        result = await self._session.execute(
            select(VacancyModel).where(VacancyModel.id == vacancy_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_source_id(
        self, source: VacancySource, source_id: str
    ) -> Vacancy | None:
        result = await self._session.execute(
            select(VacancyModel).where(
                VacancyModel.source == str(source),
                VacancyModel.source_id == source_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def create(self, vacancy: Vacancy) -> Vacancy:
        model = self._to_model(vacancy)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return self._to_domain(model)

    async def update(self, vacancy: Vacancy) -> Vacancy:
        result = await self._session.execute(
            select(VacancyModel).where(VacancyModel.id == vacancy.id)
        )
        model = result.scalar_one()
        model.title = vacancy.title
        model.company = vacancy.company
        model.description = vacancy.description
        model.requirements = vacancy.requirements
        model.city = vacancy.city
        model.work_format = str(vacancy.work_format)
        model.salary_from = vacancy.salary_from
        model.salary_to = vacancy.salary_to
        model.salary_currency = vacancy.salary_currency
        model.source_url = vacancy.source_url
        model.is_active = vacancy.is_active
        model.published_at = vacancy.published_at
        model.updated_at = vacancy.updated_at
        await self._session.flush()
        return self._to_domain(model)

    async def delete(self, vacancy_id: UUID) -> None:
        result = await self._session.execute(
            select(VacancyModel).where(VacancyModel.id == vacancy_id)
        )
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()

    async def search(
        self,
        query: str = "",
        city: str = "",
        work_format: WorkFormat | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Vacancy]:
        stmt = select(VacancyModel).where(VacancyModel.is_active.is_(True))

        if query:
            pattern = f"%{query}%"
            stmt = stmt.where(
                VacancyModel.title.ilike(pattern)
                | VacancyModel.company.ilike(pattern)
                | VacancyModel.description.ilike(pattern)
            )
        if city:
            stmt = stmt.where(VacancyModel.city.ilike(f"%{city}%"))
        if work_format:
            stmt = stmt.where(VacancyModel.work_format == str(work_format))

        stmt = stmt.order_by(VacancyModel.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_all_active(
        self, limit: int = 20, offset: int = 0
    ) -> list[Vacancy]:
        result = await self._session.execute(
            select(VacancyModel)
            .where(VacancyModel.is_active.is_(True))
            .order_by(VacancyModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_domain(m) for m in result.scalars().all()]
