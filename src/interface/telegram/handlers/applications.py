from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.use_cases.applications import (
    GetUserApplications,
    UpdateApplicationStage,
)
from src.application.use_cases.vacancies import AddManualVacancy
from src.domain.entities.application import Application
from src.domain.entities.user import User, UserProfile
from src.domain.value_objects.application_stage import ApplicationStage
from src.interface.telegram.keyboards.main import (
    application_stages_keyboard,
    applications_add_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
    skip_url_keyboard,
    stage_selection_keyboard,
    followup_keyboard,
)
from src.interface.telegram.middlewares.container import Container
from src.interface.telegram.states.forms import ManualApplicationStates

router = Router(name="applications")


# ── Мои заявки ───────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Мои заявки")
async def handle_my_applications(
    message: Message,
    user: User,
    container: Container,
) -> None:
    use_case = GetUserApplications(container.application_repo)
    applications = await use_case.execute(user_id=user.id)

    if not applications:
        await message.answer(
            "У тебя пока нет отслеживаемых вакансий.\n\n"
            "💡 Нажми «🔍 Найти стажировку» чтобы найти подходящую\n"
            "или добавь вручную:",
            reply_markup=applications_add_keyboard(),
        )
        return

    await message.answer(f"📋 <b>Твои заявки</b> ({len(applications)}):", parse_mode="HTML")

    for i, app in enumerate(applications, 1):
        a: Application = app  # type: ignore[assignment]

        title_line = (
            f"🏢 <b>{a.vacancy_title}</b> — {a.vacancy_company}"
            if a.vacancy_title
            else f"<b>Заявка #{i}</b>"
        )
        lines = [title_line, f"📊 Этап: {a.stage.label}"]
        if a.next_step:
            lines.append(f"📌 {a.next_step}")

        await message.answer(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=application_stages_keyboard(a.id),
        )

    await message.answer(
        "Добавить ещё одну заявку?",
        reply_markup=applications_add_keyboard(),
    )


# ── Обновление этапа (из карточки) ───────────────────────────────────────────

@router.callback_query(F.data.startswith("stage:"))
async def handle_stage_update(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer("Некорректные данные.", show_alert=True)
        return

    _, app_id_str, stage_value = parts

    try:
        application_id = UUID(app_id_str)
        new_stage = ApplicationStage(stage_value)
    except (ValueError, KeyError):
        await callback.answer("Неизвестный этап.", show_alert=True)
        return

    existing = await container.application_repo.get_by_id(application_id)
    if existing is None or existing.user_id != user.id:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    use_case = UpdateApplicationStage(container.application_repo)
    updated = await use_case.execute(application_id=application_id, new_stage=new_stage)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Этап обновлён: {updated.stage.label}",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


# ── AI: Сопроводительное письмо ──────────────────────────────────────────────

@router.callback_query(F.data.startswith("cover:"))
async def handle_cover_letter(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    app_id_str = (callback.data or "").split(":", 1)[1]

    try:
        application_id = UUID(app_id_str)
    except ValueError:
        await callback.answer("Некорректный ID заявки.", show_alert=True)
        return

    app = await container.application_repo.get_by_id(application_id)
    if not app or app.user_id != user.id:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    vacancy = await container.vacancy_repo.get_by_id(app.vacancy_id)
    if not vacancy:
        await callback.answer("Вакансия не найдена.", show_alert=True)
        return

    await callback.answer("Генерирую письмо...")
    await callback.message.answer(  # type: ignore[union-attr]
        f"✍️ Генерирую сопроводительное письмо для <b>{vacancy.title}</b> в {vacancy.company}...",
        parse_mode="HTML",
    )

    profile = user.profile or UserProfile(user_id=user.id)

    try:
        letter = await container.ai_service.generate_cover_letter(vacancy, profile)
        await callback.message.answer(  # type: ignore[union-attr]
            f"✍️ <b>Сопроводительное письмо</b>\n"
            f"<i>{vacancy.title} · {vacancy.company}</i>\n\n"
            f"{letter}",
            parse_mode="HTML",
        )
    except Exception as e:
        await callback.message.answer(  # type: ignore[union-attr]
            "Не удалось сгенерировать письмо. Попробуй позже."
        )


# ── Ручное добавление заявки ─────────────────────────────────────────────────

@router.callback_query(F.data == "app:add_manual")
async def start_manual_application(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "Как называется вакансия?\n\n"
        "💡 <i>Например: Аналитик данных, Junior Consultant, Marketing Intern</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(ManualApplicationStates.waiting_title)
    await callback.answer()


# ── Отмена на любом шаге ─────────────────────────────────────────────────────

@router.message(ManualApplicationStates.waiting_title, F.text == "❌ Отмена")
@router.message(ManualApplicationStates.waiting_company, F.text == "❌ Отмена")
async def cancel_manual_text(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "app:cancel")
async def cancel_manual_inline(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer("Отменено.", reply_markup=main_menu_keyboard())  # type: ignore[union-attr]
    await callback.answer()


# ── Шаг 1: Название ──────────────────────────────────────────────────────────

@router.message(ManualApplicationStates.waiting_title, F.text)
async def manual_get_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await message.answer(
        "В какую компанию?\n\n"
        "💡 <i>Можно просто название — Яндекс, McKinsey, Сбер</i>",
        parse_mode="HTML",
    )
    await state.set_state(ManualApplicationStates.waiting_company)


# ── Шаг 2: Компания ──────────────────────────────────────────────────────────

@router.message(ManualApplicationStates.waiting_company, F.text)
async def manual_get_company(message: Message, state: FSMContext) -> None:
    await state.update_data(company=message.text)
    await message.answer(
        "На каком этапе ты сейчас?\n\n"
        "💡 <i>Выбери текущий статус твоего отклика</i>",
        parse_mode="HTML",
        reply_markup=stage_selection_keyboard(),
    )
    await state.set_state(ManualApplicationStates.waiting_stage)


# ── Шаг 3: Этап ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("new_stage:"), ManualApplicationStates.waiting_stage)
async def manual_get_stage(callback: CallbackQuery, state: FSMContext) -> None:
    stage_value = (callback.data or "").split(":", 1)[1]
    await state.update_data(stage=stage_value)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        "Есть ссылка на вакансию?\n\n"
        "💡 <i>Необязательно — можно пропустить</i>",
        parse_mode="HTML",
        reply_markup=skip_url_keyboard(),
    )
    await state.set_state(ManualApplicationStates.waiting_url)
    await callback.answer()


# ── Шаг 4: Ссылка (опционально) ──────────────────────────────────────────────

@router.callback_query(F.data == "app:skip_url", ManualApplicationStates.waiting_url)
async def manual_skip_url(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await _save_manual_application(callback.message, state, user, container, url="")  # type: ignore[arg-type]
    await callback.answer()


@router.message(ManualApplicationStates.waiting_url, F.text)
async def manual_get_url(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    url = (message.text or "").strip()
    await _save_manual_application(message, state, user, container, url=url)


async def _save_manual_application(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
    url: str,
) -> None:
    fsm_data = await state.get_data()
    title = fsm_data.get("title", "")
    company = fsm_data.get("company", "")
    stage_value = fsm_data.get("stage", ApplicationStage.SAVED.value)

    use_case = AddManualVacancy(container.vacancy_repo, container.application_repo)
    application = await use_case.execute(
        user_id=user.id,
        title=title,
        company=company,
        url=url,
    )

    # Обновляем этап если не SAVED
    if stage_value != ApplicationStage.SAVED.value:
        try:
            new_stage = ApplicationStage(stage_value)
            update_uc = UpdateApplicationStage(container.application_repo)
            application = await update_uc.execute(
                application_id=application.id,
                new_stage=new_stage,
            )
        except (ValueError, Exception):
            pass

    await state.clear()
    await message.answer(
        f"✅ <b>Заявка добавлена!</b>\n"
        f"🏢 {title} — {company}\n"
        f"📊 Этап: {application.stage.label}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ── Followup callbacks (от scheduler-уведомлений) ────────────────────────────

@router.callback_query(F.data.startswith("followup:"))
async def handle_followup(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer()
        return

    _, action, app_id_str = parts

    if action == "wait":
        await callback.answer("Окей, напомним позже 👍")
        await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
        return

    try:
        application_id = UUID(app_id_str)
    except ValueError:
        await callback.answer()
        return

    stage_map = {
        "yes": ApplicationStage.SCREENING,
        "no": ApplicationStage.REJECTED,
    }
    new_stage = stage_map.get(action)
    if not new_stage:
        await callback.answer()
        return

    existing = await container.application_repo.get_by_id(application_id)
    if not existing or existing.user_id != user.id:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return

    use_case = UpdateApplicationStage(container.application_repo)
    updated = await use_case.execute(application_id=application_id, new_stage=new_stage)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Этап обновлён: {updated.stage.label}",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("interview:ready:"))
async def handle_interview_ready(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.answer("Удачи на интервью! 💪")


@router.callback_query(F.data == "digest:search")
async def handle_digest_search(callback: CallbackQuery) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "Нажми «🔍 Найти стажировку» в меню для просмотра подборки.",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
