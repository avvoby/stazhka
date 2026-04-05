from uuid import UUID

from src.domain.entities.vacancy import Vacancy
from src.domain.repositories.application_repo import ApplicationRepository
from src.domain.repositories.vacancy_repo import VacancyRepository
from src.infrastructure.ai.mock_session import MAX_QUESTIONS, MockSessionRepository


class RateLimiter:
    """Заглушка rate limiter. Будет реализована через Redis."""

    async def check(self, user_id: UUID, feature: str) -> bool:
        return True


class GenerateCoverLetter:
    """Генерирует сопроводительное письмо для конкретного отклика через Claude."""

    def __init__(
        self,
        ai_service: object,
        application_repo: ApplicationRepository,
        vacancy_repo: VacancyRepository,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._ai_service = ai_service
        self._application_repo = application_repo
        self._vacancy_repo = vacancy_repo
        self._rate_limiter = rate_limiter or RateLimiter()

    async def execute(self, user_id: UUID, application_id: UUID) -> str:
        await self._rate_limiter.check(user_id, "cover_letter")

        application = await self._application_repo.get_by_id(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")
        if application.user_id != user_id:
            raise PermissionError("Application does not belong to this user")

        vacancy = await self._vacancy_repo.get_by_id(application.vacancy_id)
        if vacancy is None:
            raise ValueError(f"Vacancy {application.vacancy_id} not found")

        cover_letter: str = await self._ai_service.generate_cover_letter(  # type: ignore[attr-defined]
            vacancy=vacancy,
            profile=None,
        )
        return cover_letter


class MockInterviewUseCase:
    """Полный flow mock-интервью: 5 вопросов, анализ каждого ответа, итоговый отчёт."""

    def __init__(
        self,
        ai_service: object,
        application_repo: ApplicationRepository,
        vacancy_repo: VacancyRepository,
        mock_session_repo: MockSessionRepository,
    ) -> None:
        self._ai = ai_service
        self._application_repo = application_repo
        self._vacancy_repo = vacancy_repo
        self._sessions = mock_session_repo

    async def start(self, user_id: UUID, application_id: UUID) -> dict:
        """
        Запускает сессию mock-интервью.
        Возвращает:
          {session_id, question, vacancy_title, company, question_num=1}
        """
        application = await self._application_repo.get_by_id(application_id)
        if application is None:
            raise ValueError(f"Application {application_id} not found")
        if application.user_id != user_id:
            raise PermissionError("Application does not belong to this user")

        vacancy = await self._vacancy_repo.get_by_id(application.vacancy_id)
        if vacancy is None:
            raise ValueError(f"Vacancy {application.vacancy_id} not found")

        session_id = await self._sessions.create(
            user_id=user_id,
            vacancy_id=vacancy.id,
            vacancy_title=vacancy.title,
            company=vacancy.company,
            description=vacancy.description[:1500],
            requirements=vacancy.requirements[:800],
        )

        first_question: str = await self._ai.generate_mock_question(  # type: ignore[attr-defined]
            vacancy=vacancy,
            question_number=1,
            history=[],
        )

        session = await self._sessions.get(user_id, session_id)
        if session:
            session["current_question"] = first_question
            await self._sessions.save(user_id, session_id, session)

        return {
            "session_id": session_id,
            "question": first_question,
            "vacancy_title": vacancy.title,
            "company": vacancy.company,
            "question_num": 1,
        }

    async def submit_answer(
        self,
        user_id: UUID,
        session_id: str,
        answer: str,
    ) -> dict:
        """
        Принимает ответ на текущий вопрос, возвращает анализ и следующий вопрос или отчёт.
        Возвращает:
          {
            analysis: {strengths, improvements, ideal_answer_hint},
            question_num: int,   # номер только что отвеченного вопроса
            is_final: bool,
            next_question: str | None,
            report: str | None,  # только если is_final=True
            vacancy_title: str,
            company: str,
          }
        """
        session = await self._sessions.get(user_id, session_id)
        if session is None:
            raise ValueError("Session not found or expired")

        current_question = session["current_question"]
        question_num = session["question_num"]

        # Реконструируем Vacancy из данных сессии
        vacancy = Vacancy(
            title=session["vacancy_title"],
            company=session["company"],
            description=session["description"],
            requirements=session["requirements"],
        )

        # Анализируем ответ
        analysis: dict = await self._ai.analyze_mock_answer(  # type: ignore[attr-defined]
            question=current_question,
            answer=answer,
            vacancy=vacancy,
        )

        # Добавляем в историю
        session["history"].append({"question": current_question, "answer": answer})
        is_final = question_num >= MAX_QUESTIONS

        result: dict = {
            "analysis": analysis,
            "question_num": question_num,
            "is_final": is_final,
            "next_question": None,
            "report": None,
            "vacancy_title": session["vacancy_title"],
            "company": session["company"],
        }

        if is_final:
            report: str = await self._ai.generate_mock_report(  # type: ignore[attr-defined]
                history=session["history"],
                vacancy_title=session["vacancy_title"],
                company=session["company"],
            )
            result["report"] = report
            session["is_finished"] = True
            await self._sessions.save(user_id, session_id, session)
            await self._sessions.delete(user_id, session_id)
        else:
            next_num = question_num + 1
            next_question: str = await self._ai.generate_mock_question(  # type: ignore[attr-defined]
                vacancy=vacancy,
                question_number=next_num,
                history=session["history"],
            )
            session["question_num"] = next_num
            session["current_question"] = next_question
            await self._sessions.save(user_id, session_id, session)
            result["next_question"] = next_question

        return result
