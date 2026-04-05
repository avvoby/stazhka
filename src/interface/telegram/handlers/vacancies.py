import asyncio
from typing import Any

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.application.services.matching_service import MatchingService, ScoredVacancy
from src.application.services.vacancy_aggregator import VacancyAggregator
from src.application.use_cases.vacancies import AddManualVacancy, AddVacancyFromURL
from src.domain.entities.application import Application
from src.domain.entities.user import User
from src.domain.value_objects.vacancy_source import VacancySource
from src.interface.telegram.keyboards.main import (
    SPEC_LABELS,
    SKILL_LABELS,
    cancel_keyboard,
    main_menu_keyboard,
    search_change_keyboard,
    search_settings_keyboard,
    skills_keyboard,
    specialization_keyboard,
    vacancy_card_keyboard,
    vacancies_more_keyboard,
)
from src.interface.telegram.middlewares.container import Container
from src.interface.telegram.states.forms import AddVacancyStates, QuickSearchStates

router = Router(name="vacancies")

PAGE_SIZE = 5


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_salary(v: dict[str, Any]) -> str:
    from_ = v.get("salary_from")
    to_ = v.get("salary_to")
    currency = v.get("currency", "RUB")
    sym = "₽" if currency == "RUB" else currency
    if from_ and to_:
        return f"{from_:,}–{to_:,} {sym}".replace(",", " ")
    if from_:
        return f"от {from_:,} {sym}".replace(",", " ")
    if to_:
        return f"до {to_:,} {sym}".replace(",", " ")
    return "не указана"


def _card_text(sv: ScoredVacancy) -> str:
    v = sv.vacancy
    salary = _format_salary(v)
    city = v.get("city") or "не указан"

    lines = [
        f"🏢 <b>{v.get('title', '')}</b> — {v.get('company', '')}",
        f"📍 {city} | 💰 {salary}",
    ]

    score = sv.final_score
    if score > 0:
        lines.append(f"🎯 Совпадение: {score}%")
    if sv.reason:
        lines.append(f"💬 <i>{sv.reason}</i>")

    return "\n".join(lines)


async def _send_scored_cards(
    message: Message,
    scored: list[ScoredVacancy],
    offset: int,
) -> None:
    page = scored[offset: offset + PAGE_SIZE]
    for sv in page:
        v = sv.vacancy
        url = v.get("url") or None
        source_id = v.get("source_id", "")
        # Для hh.ru передаём url в кнопку "Открыть", для остальных — только в apply
        hh_url = url if v.get("source") == "hh" else None

        await message.answer(
            _card_text(sv),
            reply_markup=vacancy_card_keyboard(source_id, hh_url, show_feedback=True),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    next_offset = offset + PAGE_SIZE
    if next_offset < len(scored):
        await message.answer(
            f"Показано {next_offset} из {len(scored)}",
            reply_markup=vacancies_more_keyboard(next_offset),
        )


# ── Поиск (общий хелпер) ──────────────────────────────────────────────────────

async def _run_search(message: Message, state: FSMContext, user: User, container: Container) -> None:
    """Запускает полный цикл поиска и показывает карточки. Используется из нескольких мест."""
    # Перезагружаем профиль — он мог измениться в quick-edit flow
    fresh_profile = await container.user_repo.get_profile(user.id)
    profile = fresh_profile or user.profile

    aggregator = VacancyAggregator(
        hh_client=container.hh_client,
        superjob_client=container.superjob_client,
        telegram_parser=container.telegram_parser,
    )
    all_vacancies, disliked_ids = await asyncio.gather(
        aggregator.fetch_all(profile),
        container.feedback_repo.get_disliked_ids(user.id),
    )

    disliked_set = set(disliked_ids)
    all_vacancies = [v for v in all_vacancies if v.get("source_id") not in disliked_set]

    if not all_vacancies:
        await message.answer(
            "Ничего не нашлось 😔\n"
            "Попробуй обновить профиль или зайди позже.",
            reply_markup=main_menu_keyboard(),
        )
        return

    matcher = MatchingService(ai_service=container.ai_service)
    top = await matcher.match(all_vacancies, profile)

    if not top:
        top = [ScoredVacancy(vacancy=v, source=v.get("source", "")) for v in all_vacancies]

    serialized = [
        {
            "vacancy": sv.vacancy,
            "keyword_score": sv.keyword_score,
            "claude_score": sv.claude_score,
            "reason": sv.reason,
            "source": sv.source,
        }
        for sv in top
    ]
    await state.update_data(scored_list=serialized)
    await _send_scored_cards(message, top, offset=0)
    await message.answer("Хочешь скорректировать поиск?", reply_markup=search_change_keyboard())


# ── Найти стажировку ─────────────────────────────────────────────────────────

@router.message(F.text == "🔍 Найти стажировку")
async def handle_find_vacancy(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    await state.clear()
    await message.answer("🔍 Ищу подходящие стажировки...")
    await _run_search(message, state, user, container)


# ── Показать ещё ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("vacancies:more:"))
async def handle_more_vacancies(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    offset = int((callback.data or "").split(":")[-1])
    fsm_data = await state.get_data()
    raw_list: list[dict[str, Any]] = fsm_data.get("scored_list", [])

    if not raw_list:
        await callback.answer("Результаты устарели. Нажми «Найти стажировку» заново.", show_alert=True)
        return

    scored = [
        ScoredVacancy(
            vacancy=item["vacancy"],
            keyword_score=item["keyword_score"],
            claude_score=item["claude_score"],
            reason=item["reason"],
            source=item["source"],
        )
        for item in raw_list
    ]

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await _send_scored_cards(callback.message, scored, offset=offset)  # type: ignore[arg-type]
    await callback.answer()


# ── Обратная связь по вакансии ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("fb:"))
async def handle_vacancy_feedback(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    parts = (callback.data or "").split(":")
    if len(parts) != 3:
        await callback.answer()
        return

    _, feedback, source_id = parts
    labels = {"like": "⭐ Сохранено", "dislike": "👎 Скрыто", "apply": "✅ Отклик отмечен"}
    label = labels.get(feedback, "Ок")

    # Сохраняем фидбэк (best-effort, не критично)
    try:
        await container.feedback_repo.upsert(
            user_id=user.id,
            source_id=source_id,
            feedback=feedback,
        )
    except Exception:
        pass

    await callback.answer(label)


# ── Quick-edit поиска ────────────────────────────────────────────────────────

@router.callback_query(F.data == "search:settings")
async def handle_search_settings(callback: CallbackQuery) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        "Что изменим?",
        reply_markup=search_settings_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "search:spec")
async def handle_search_spec(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        "Выбери специализацию для поиска:",
        reply_markup=specialization_keyboard(),
    )
    await state.set_state(QuickSearchStates.editing_city)  # временно используем как флаг ожидания spec
    await state.update_data(quick_edit="spec")
    await callback.answer()


@router.callback_query(F.data.startswith("spec:"), QuickSearchStates.editing_city)
async def handle_quick_spec_selected(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    fsm = await state.get_data()
    if fsm.get("quick_edit") != "spec":
        return

    spec_key = (callback.data or "").split(":", 1)[1]
    spec_label = SPEC_LABELS.get(spec_key, spec_key)

    profile = user.profile
    if profile:
        profile.specialty = spec_label
        await container.user_repo.upsert_profile(profile)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await state.update_data(quick_edit=None)
    await state.set_state(None)

    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Специализация: {spec_label}\n🔍 Ищу заново..."
    )
    await callback.answer()
    await _run_search(callback.message, state, user, container)  # type: ignore[arg-type]


@router.callback_query(F.data == "search:skills")
async def handle_search_skills(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    current = user.profile.skills if user.profile else []
    # Переводим labels обратно в keys для multiselect
    current_keys = [k for k, v in SKILL_LABELS.items() if v in current]
    await callback.message.answer(  # type: ignore[union-attr]
        "Выбери навыки (можно несколько):",
        reply_markup=skills_keyboard(current_keys),
    )
    await state.set_state(QuickSearchStates.editing_city)
    await state.update_data(quick_edit="skills", quick_skills=current_keys)
    await callback.answer()


@router.callback_query(F.data.startswith("skill:"), QuickSearchStates.editing_city)
async def handle_quick_skill_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    fsm = await state.get_data()
    if fsm.get("quick_edit") != "skills":
        return

    skill_key = (callback.data or "").split(":", 1)[1]
    selected: list[str] = list(fsm.get("quick_skills", []))
    if skill_key in selected:
        selected.remove(skill_key)
    else:
        selected.append(skill_key)

    await state.update_data(quick_skills=selected)
    await callback.message.edit_reply_markup(reply_markup=skills_keyboard(selected))  # type: ignore[union-attr]
    await callback.answer()


@router.callback_query(F.data == "skills:done", QuickSearchStates.editing_city)
async def handle_quick_skills_done(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    fsm = await state.get_data()
    if fsm.get("quick_edit") != "skills":
        return

    selected_keys: list[str] = fsm.get("quick_skills", [])
    skill_labels = [SKILL_LABELS.get(k, k) for k in selected_keys]

    profile = user.profile
    if profile:
        profile.skills = skill_labels
        await container.user_repo.upsert_profile(profile)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await state.update_data(quick_edit=None, quick_skills=None)
    await state.set_state(None)

    skills_str = ", ".join(skill_labels) if skill_labels else "не выбраны"
    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Навыки: {skills_str}\n🔍 Ищу заново..."
    )
    await callback.answer()
    await _run_search(callback.message, state, user, container)  # type: ignore[arg-type]


@router.callback_query(F.data == "search:city")
async def handle_search_city(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        "Введи город (например: Москва, Санкт-Петербург):",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(QuickSearchStates.editing_city)
    await state.update_data(quick_edit="city")
    await callback.answer()


@router.message(QuickSearchStates.editing_city, F.text)
async def handle_quick_city_input(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    fsm = await state.get_data()
    if fsm.get("quick_edit") != "city":
        return

    city = (message.text or "").strip()
    if city == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu_keyboard())
        return

    profile = user.profile
    if profile:
        profile.desired_city = city
        await container.user_repo.upsert_profile(profile)

    await state.update_data(quick_edit=None)
    await state.set_state(None)
    await message.answer(f"✅ Город: {city}\n🔍 Ищу заново...", reply_markup=main_menu_keyboard())
    await _run_search(message, state, user, container)


@router.callback_query(F.data == "search:reset")
async def handle_search_reset(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    profile = user.profile
    if profile:
        profile.specialty = ""
        profile.skills = []
        profile.desired_city = ""
        await container.user_repo.upsert_profile(profile)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer("🔄 Фильтры сброшены. 🔍 Ищу заново...")  # type: ignore[union-attr]
    await callback.answer()
    await _run_search(callback.message, state, user, container)  # type: ignore[arg-type]


# ── Добавить в заявки (с карточки) ───────────────────────────────────────────

@router.callback_query(F.data.startswith("apply:"))
async def handle_apply_from_card(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    source_id = (callback.data or "").split(":", 1)[1]

    await callback.answer("Добавляю...")

    # Проверяем — вдруг вакансия уже есть в БД
    existing_vacancy = await container.vacancy_repo.get_by_source_id(
        VacancySource.HH_RU, source_id
    )
    if existing_vacancy:
        saved_vacancy = existing_vacancy
    else:
        raw = await container.hh_client.get_vacancy(source_id)
        if not raw:
            await callback.answer("Не удалось загрузить вакансию. Попробуй позже.", show_alert=True)
            return
        saved_vacancy = await container.vacancy_repo.create(
            container.hh_client.vacancy_to_domain(raw)
        )

    # Проверяем — вдруг пользователь уже добавил эту вакансию
    existing_app = await container.application_repo.get_by_user_and_vacancy(
        user.id, saved_vacancy.id
    )
    if existing_app:
        await callback.answer("Эта вакансия уже в твоих заявках!", show_alert=True)
        return

    application = Application(user_id=user.id, vacancy_id=saved_vacancy.id)
    saved_app = await container.application_repo.create(application)

    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Добавлено в заявки!\n"
        f"🏢 <b>{saved_vacancy.title}</b> — {saved_vacancy.company}\n"
        f"📊 Этап: {saved_app.stage.label}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


# ── Добавить вакансию вручную (из меню) ──────────────────────────────────────

@router.message(F.text == "➕ Добавить вакансию")
async def handle_add_vacancy_manual(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Как называется вакансия?\n\n"
        "💡 <i>Например: Аналитик данных, Junior Consultant, Marketing Intern</i>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(AddVacancyStates.waiting_manual_title)


@router.message(AddVacancyStates.waiting_manual_title, F.text == "❌ Отмена")
@router.message(AddVacancyStates.waiting_manual_company, F.text == "❌ Отмена")
async def cancel_manual(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu_keyboard())


@router.message(AddVacancyStates.waiting_manual_title, F.text)
async def handle_manual_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text)
    await message.answer(
        "В какую компанию?\n\n"
        "💡 <i>Можно просто название — Яндекс, McKinsey, Сбер</i>",
        parse_mode="HTML",
    )
    await state.set_state(AddVacancyStates.waiting_manual_company)


@router.message(AddVacancyStates.waiting_manual_company, F.text)
async def handle_manual_company(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    fsm_data = await state.get_data()
    title = fsm_data.get("title", "")
    company = message.text or ""

    use_case = AddManualVacancy(container.vacancy_repo, container.application_repo)
    application = await use_case.execute(
        user_id=user.id,
        title=title,
        company=company,
    )
    await state.clear()
    await message.answer(
        f"✅ Вакансия добавлена!\n"
        f"🏢 <b>{title}</b> — {company}\n"
        f"📊 Этап: {application.stage.label}",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )


# ── URL flow ──────────────────────────────────────────────────────────────────

@router.message(AddVacancyStates.waiting_url, F.text == "❌ Отмена")
async def cancel_url(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu_keyboard())


@router.message(AddVacancyStates.waiting_url, F.text)
async def handle_url(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    url = (message.text or "").strip()
    try:
        use_case = AddVacancyFromURL(
            container.hh_client,
            container.vacancy_repo,
            container.application_repo,
        )
        application = await use_case.execute(user_id=user.id, url=url)
        await state.clear()
        await message.answer(
            f"✅ Вакансия добавлена!\nЭтап: {application.stage.label}",
            reply_markup=main_menu_keyboard(),
        )
    except Exception:
        await message.answer(
            "Не удалось распознать ссылку. Попробуй ещё раз или добавь вручную.",
        )
