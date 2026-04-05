"""
Handlers для AI-функций: mock-интервью и cover letter (из карточки заявки).
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.use_cases.ai_features import MockInterviewUseCase
from src.application.use_cases.applications import GetUserApplications
from src.domain.entities.user import User
from src.interface.telegram.keyboards.main import (
    main_menu_keyboard,
    mock_finish_keyboard,
    mock_select_keyboard,
)
from src.interface.telegram.middlewares.container import Container
from src.interface.telegram.states.forms import MockInterviewStates

router = Router(name="ai_features")

MAX_QUESTIONS = 5


# ── Утилиты ───────────────────────────────────────────────────────────────────

def _analysis_text(analysis: dict, question_num: int) -> str:
    strengths = analysis.get("strengths") or "—"
    improvements = analysis.get("improvements") or "—"
    hint = analysis.get("ideal_answer_hint") or "—"
    return (
        f"<b>Разбор ответа #{question_num}:</b>\n\n"
        f"✅ <b>Сильное:</b> {strengths}\n\n"
        f"⚠️ <b>Улучшить:</b> {improvements}\n\n"
        f"💡 <b>Идеальный ответ:</b> {hint}"
    )


def _report_text(report: str, company: str) -> str:
    return (
        f"📊 <b>Итоги mock-интервью — {company}</b>\n\n"
        f"{report}"
    )


# ── Запуск mock-интервью из списка заявок ─────────────────────────────────────

@router.message(F.text == "🎤 Mock-интервью")
async def handle_mock_menu(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    """Точка входа из ReplyKeyboard меню."""
    await state.clear()
    use_case = GetUserApplications(container.application_repo)
    applications = await use_case.execute(user_id=user.id)

    active = [a for a in applications if a.is_active]  # type: ignore[union-attr]
    if not active:
        await message.answer(
            "У тебя нет активных заявок для mock-интервью.\n\n"
            "Добавь вакансию через «📋 Мои заявки» и возвращайся.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        "Выбери вакансию для mock-интервью:",
        reply_markup=mock_select_keyboard(active),
    )
    await state.set_state(MockInterviewStates.choosing_vacancy)


# ── Запуск с конкретной заявкой (из карточки или из списка) ──────────────────

@router.callback_query(F.data.startswith("mock:app:"))
async def handle_mock_start(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    from uuid import UUID
    app_id_str = (callback.data or "").split("mock:app:", 1)[1]

    try:
        application_id = UUID(app_id_str)
    except ValueError:
        await callback.answer("Некорректный ID.", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.answer()

    use_case = MockInterviewUseCase(
        ai_service=container.ai_service,
        application_repo=container.application_repo,
        vacancy_repo=container.vacancy_repo,
        mock_session_repo=container.mock_session_repo,
    )

    try:
        result = await use_case.start(user_id=user.id, application_id=application_id)
    except (ValueError, PermissionError) as e:
        await callback.message.answer(str(e), reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
        return

    await state.set_state(MockInterviewStates.waiting_answer)
    await state.update_data(
        session_id=result["session_id"],
        vacancy_title=result["vacancy_title"],
        company=result["company"],
        application_id=app_id_str,
    )

    await callback.message.answer(  # type: ignore[union-attr]
        f"🎤 <b>Mock-интервью: {result['company']}</b>\n"
        f"<i>{result['vacancy_title']}</i>\n\n"
        "Я буду задавать вопросы как HR. Отвечай развёрнуто.\n\n"
        f"<b>Вопрос 1 из {MAX_QUESTIONS}:</b>\n\n"
        f"{result['question']}",
        parse_mode="HTML",
    )


@router.callback_query(F.data == "mock:cancel")
async def handle_mock_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer("Отменено.", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()


# ── Приём ответа ──────────────────────────────────────────────────────────────

@router.message(MockInterviewStates.waiting_answer, F.text)
async def handle_mock_answer(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    answer = (message.text or "").strip()
    if not answer:
        return

    fsm = await state.get_data()
    session_id: str = fsm.get("session_id", "")
    company: str = fsm.get("company", "")

    use_case = MockInterviewUseCase(
        ai_service=container.ai_service,
        application_repo=container.application_repo,
        vacancy_repo=container.vacancy_repo,
        mock_session_repo=container.mock_session_repo,
    )

    try:
        result = await use_case.submit_answer(
            user_id=user.id,
            session_id=session_id,
            answer=answer,
        )
    except ValueError:
        await message.answer(
            "Сессия устарела. Начни mock-интервью заново.",
            reply_markup=main_menu_keyboard(),
        )
        await state.clear()
        return

    question_num = result["question_num"]

    # Показываем анализ текущего ответа
    await message.answer(
        _analysis_text(result["analysis"], question_num),
        parse_mode="HTML",
    )

    if result["is_final"]:
        # Показываем итоговый отчёт
        await state.clear()
        await message.answer(
            _report_text(result["report"] or "", company),
            parse_mode="HTML",
            reply_markup=mock_finish_keyboard(),
        )
    else:
        next_num = question_num + 1
        await message.answer(
            f"<b>Вопрос {next_num} из {MAX_QUESTIONS}:</b>\n\n"
            f"{result['next_question']}",
            parse_mode="HTML",
        )


# ── Кнопки финального экрана ─────────────────────────────────────────────────

@router.callback_query(F.data == "mock:to_menu")
async def handle_mock_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer("Главное меню:", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "mock:to_apps")
async def handle_mock_to_apps(callback: CallbackQuery, state: FSMContext, message: Message) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    # Имитируем нажатие «Мои заявки»
    await callback.message.answer("📋 Переходи в «Мои заявки»", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "mock:restart")
async def handle_mock_restart(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]

    from src.application.use_cases.applications import GetUserApplications
    use_case = GetUserApplications(container.application_repo)
    applications = await use_case.execute(user_id=user.id)
    active = [a for a in applications if a.is_active]  # type: ignore[union-attr]

    if not active:
        await callback.message.answer("Нет активных заявок.", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
        await callback.answer()
        return

    await callback.message.answer(  # type: ignore[union-attr]
        "Выбери вакансию для нового mock-интервью:",
        reply_markup=mock_select_keyboard(active),
    )
    await state.set_state(MockInterviewStates.choosing_vacancy)
    await callback.answer()
