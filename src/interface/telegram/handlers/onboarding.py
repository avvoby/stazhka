from datetime import datetime

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from src.application.use_cases.applications import GetUserApplications
from src.application.use_cases.onboarding import GetOrCreateUser
from src.domain.entities.user import User, UserProfile
from src.domain.value_objects.application_stage import ApplicationStage
from src.interface.telegram.keyboards.main import (
    COURSE_LABELS,
    SKILL_LABELS,
    SPEC_LABELS,
    cancel_keyboard,
    course_keyboard,
    main_menu_keyboard,
    profile_edit_v2_keyboard,
    profile_edit_keyboard,
    profile_v2_keyboard,
    skills_keyboard,
    specialization_keyboard,
)
from src.interface.telegram.middlewares.container import Container
from src.interface.telegram.states.forms import OnboardingStates, ProfileEditStates

router = Router(name="onboarding")

# ── Тексты ───────────────────────────────────────────────────────────────────

PRIVACY_TEXT = (
    "👋 Привет! Я Стажка — помогаю студентам находить стажировки и отслеживать отклики.\n\n"
    "Для работы мне нужно хранить твои данные (специализация, навыки, желаемые компании). "
    "Я не передаю их третьим лицам.\n\n"
    "Принимаешь условия?"
)

SPEC_TEXT = (
    "Выбери свою специализацию:\n\n"
    "💡 <i>Это поможет подбирать вакансии именно под тебя</i>"
)

COURSE_TEXT = (
    "На каком ты курсе?\n\n"
    "💡 <i>Некоторые компании берут только с 3 курса — учтём это</i>"
)

SKILLS_TEXT = (
    "Выбери свои навыки (можно несколько):\n\n"
    "💡 <i>Покажем только те вакансии, где твои навыки совпадают</i>"
)

COMPANIES_TEXT = (
    "Напиши компании или типы работодателей — можно несколько через запятую.\n"
    "Например: <i>McKinsey, Яндекс, банки, стартапы</i>\n\n"
    "💡 <i>Пришлём уведомление как только там появится подходящая вакансия</i>"
)


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _save_profile(user_id: object, fsm_data: dict, container: Container) -> None:
    """Сохраняет структурированный профиль из FSM-данных."""
    spec = fsm_data.get("specialization", "")
    course = fsm_data.get("course", "")
    skills = fsm_data.get("skills", [])
    companies = fsm_data.get("companies", "")

    about = (
        f"Специализация: {SPEC_LABELS.get(spec, spec)}\n"
        f"Курс: {COURSE_LABELS.get(course, course)}\n"
        f"Навыки: {', '.join(SKILL_LABELS.get(s, s) for s in skills)}\n"
        f"Компании мечты: {companies or 'не указаны'}"
    )

    profile = await container.user_repo.get_profile(user_id)  # type: ignore[arg-type]
    if profile is None:
        profile = UserProfile(user_id=user_id)  # type: ignore[arg-type]

    profile.specialty = SPEC_LABELS.get(spec, spec)
    profile.skills = [SKILL_LABELS.get(s, s) for s in skills]
    profile.about = about
    profile.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(profile)


# ── /menu ────────────────────────────────────────────────────────────────────

@router.message(Command("menu"))
async def cmd_menu(message: Message, user: object) -> None:
    u: User = user  # type: ignore[assignment]
    name = u.display_name or ""
    await message.answer(
        f"Главное меню, {name} 👇",
        reply_markup=main_menu_keyboard(),
    )


# ── /start ───────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(
    message: Message, state: FSMContext, user: object, container: Container
) -> None:
    u: User = user  # type: ignore[assignment]
    await state.clear()

    name = u.display_name or (message.from_user.first_name if message.from_user else "")

    if u.profile and u.profile.about:
        await message.answer(
            f"С возвращением, {name}! 👋",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(
        f"Привет, {name}! 👋\n\n"
        "Нажимая «Продолжить», ты соглашаешься\n"
        "с условиями использования сервиса.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="✅ Продолжить", callback_data="onboard_accept")
        ]]),
    )
    await state.set_state(OnboardingStates.waiting_privacy)


# ── Принятие условий ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "onboard_accept")
async def handle_onboard_accept(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        "Добро пожаловать! 🎉\n\nВыбери, что тебя интересует:",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


# ── Шаг 1: Специализация (онбординг, если запустят /start повторно) ──────────

@router.callback_query(F.data == "privacy:accept", OnboardingStates.waiting_privacy)
async def accept_privacy(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        SPEC_TEXT,
        reply_markup=specialization_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_specialization)
    await callback.answer()


# ── Шаг 2: Специализация ─────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("spec:"), OnboardingStates.waiting_specialization)
async def set_specialization(callback: CallbackQuery, state: FSMContext) -> None:
    spec_key = callback.data.split(":")[1]  # type: ignore[union-attr]
    await state.update_data(specialization=spec_key)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        COURSE_TEXT,
        reply_markup=course_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_course)
    await callback.answer()


# ── Шаг 3: Курс ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("course:"), OnboardingStates.waiting_course)
async def set_course(callback: CallbackQuery, state: FSMContext) -> None:
    course_key = callback.data.split(":")[1]  # type: ignore[union-attr]
    await state.update_data(course=course_key, skills=[])

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        SKILLS_TEXT,
        reply_markup=skills_keyboard([]),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_skills)
    await callback.answer()


# ── Шаг 4: Навыки (мультиселект) ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("skill:"), OnboardingStates.waiting_skills)
async def toggle_skill(callback: CallbackQuery, state: FSMContext) -> None:
    skill_key = callback.data.split(":")[1]  # type: ignore[union-attr]
    fsm_data = await state.get_data()
    selected: list[str] = list(fsm_data.get("skills", []))

    if skill_key in selected:
        selected.remove(skill_key)
    else:
        selected.append(skill_key)

    await state.update_data(skills=selected)
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=skills_keyboard(selected)
    )
    await callback.answer()


@router.callback_query(F.data == "skills:done", OnboardingStates.waiting_skills)
async def confirm_skills(callback: CallbackQuery, state: FSMContext) -> None:
    fsm_data = await state.get_data()
    selected: list[str] = fsm_data.get("skills", [])

    if not selected:
        await callback.answer("Выбери хотя бы один навык!", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        COMPANIES_TEXT,
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.waiting_companies)
    await callback.answer()


# ── Шаг 5: Компании ──────────────────────────────────────────────────────────

@router.message(OnboardingStates.waiting_companies, F.text == "❌ Отмена")
async def cancel_onboarding(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Онбординг отменён. Напиши /start чтобы начать заново.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(OnboardingStates.waiting_companies, F.text)
async def save_companies(
    message: Message,
    state: FSMContext,
    user: object,
    container: Container,
) -> None:
    u: User = user  # type: ignore[assignment]
    await state.update_data(companies=message.text or "")
    fsm_data = await state.get_data()

    await _save_profile(u.id, fsm_data, container)
    await state.clear()

    skills = fsm_data.get("skills", [])
    skills_str = ", ".join(SKILL_LABELS.get(s, s) for s in skills)
    spec = SPEC_LABELS.get(fsm_data.get("specialization", ""), "")

    await message.answer(
        f"Готово! Профиль сохранён 🎉\n\n"
        f"🎓 <b>{spec}</b> · {COURSE_LABELS.get(fsm_data.get('course', ''), '')}\n"
        f"💡 {skills_str}\n\n"
        f"Чем займёмся?",
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


# ── Профиль v2 ───────────────────────────────────────────────────────────────

def _extract_about_field(about: str, prefix: str) -> str:
    for line in (about or "").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return ""


async def _build_profile_text(user: User, container: Container) -> str:
    u = user
    p = u.profile

    # Статистика заявок
    apps_uc = GetUserApplications(container.application_repo)
    applications = await apps_uc.execute(user_id=u.id)

    total = len(applications)
    by_stage: dict[str, int] = {}
    for a in applications:
        by_stage[str(a.stage)] = by_stage.get(str(a.stage), 0) + 1  # type: ignore[union-attr]

    active = sum(1 for a in applications if a.is_active)  # type: ignore[union-attr]
    applied = by_stage.get(ApplicationStage.APPLIED, 0)
    interview = by_stage.get(ApplicationStage.INTERVIEW, 0)
    offer = by_stage.get(ApplicationStage.OFFER, 0)

    # Профиль
    skills_str = ", ".join(p.skills) if (p and p.skills) else "не указаны"
    course_str = _extract_about_field(p.about if p else "", "Курс:") or "не указан"
    companies_str = _extract_about_field(p.about if p else "", "Компании мечты:") or "не указаны"
    spec = (p.specialty if p else "") or "не указана"
    gpa_str = str(p.gpa) if (p and p.gpa) else "не указан"
    lang_str = (p.language if p else "") or "не указан"

    return (
        f"👤 <b>Личный кабинет</b>\n\n"
        f"<b>📊 Статистика</b>\n"
        f"  Активных заявок: {active}\n"
        f"  Подано: {applied} · Интервью: {interview} · Офферов: {offer}\n\n"
        f"<b>👤 Мой профиль</b>\n"
        f"  🎓 {spec} · {course_str}\n"
        f"  💡 Навыки: {skills_str}\n"
        f"  🏢 Компании: {companies_str}\n"
        f"  📊 GPA: {gpa_str}\n"
        f"  🌍 Язык: {lang_str}\n\n"
        f"<b>⚙️ Настройки</b>"
    )


@router.message(F.text == "👤 Профиль")
async def handle_profile(
    message: Message, user: object, container: Container
) -> None:
    u: User = user  # type: ignore[assignment]

    if not u.profile or not u.profile.specialty:
        await message.answer(
            "Профиль не заполнен. Напиши /start чтобы пройти регистрацию."
        )
        return

    text = await _build_profile_text(u, container)
    notif_on = u.profile.notifications_enabled if u.profile else True
    await message.answer(text, reply_markup=profile_v2_keyboard(notif_on), parse_mode="HTML")


# ── Прогресс ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile:progress")
async def handle_progress(
    callback: CallbackQuery,
    user: object,
    container: Container,
) -> None:
    u: User = user  # type: ignore[assignment]
    apps_uc = GetUserApplications(container.application_repo)
    applications = await apps_uc.execute(user_id=u.id)

    by_stage: dict[str, int] = {}
    for a in applications:
        by_stage[str(a.stage)] = by_stage.get(str(a.stage), 0) + 1  # type: ignore[union-attr]

    def s(stage: ApplicationStage) -> int:
        return by_stage.get(str(stage), 0)

    applied = s(ApplicationStage.APPLIED)
    interview = s(ApplicationStage.INTERVIEW)
    conversion = round(interview / applied * 100) if applied else 0

    text = (
        f"📈 <b>Твой прогресс</b>\n\n"
        f"<b>Воронка:</b>\n"
        f"  💾 Сохранено: {s(ApplicationStage.SAVED)}\n"
        f"  📤 Подано: {applied}\n"
        f"  🔍 Скрининг: {s(ApplicationStage.SCREENING)}\n"
        f"  📝 Тест: {s(ApplicationStage.TEST)}\n"
        f"  🎙 Интервью: {interview}\n"
        f"  🎉 Оффер: {s(ApplicationStage.OFFER)}\n"
        f"  ❌ Отказ: {s(ApplicationStage.REJECTED)}\n\n"
        f"📊 Конверсия подача→интервью: {conversion}%\n"
        f"🔥 Активных сессий: {sum(1 for a in applications if a.is_active)}"  # type: ignore[union-attr]
    )

    await callback.message.answer(text, parse_mode="HTML")  # type: ignore[union-attr]
    await callback.answer()


# ── Уведомления toggle ────────────────────────────────────────────────────────

@router.callback_query(F.data == "profile:toggle_notif")
async def handle_toggle_notif(
    callback: CallbackQuery,
    user: object,
    container: Container,
) -> None:
    u: User = user  # type: ignore[assignment]
    p = u.profile
    if not p:
        await callback.answer("Профиль не найден.", show_alert=True)
        return

    p.notifications_enabled = not p.notifications_enabled
    p.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(p)

    text = await _build_profile_text(u, container)
    await callback.message.edit_text(  # type: ignore[union-attr]
        text,
        reply_markup=profile_v2_keyboard(p.notifications_enabled),
        parse_mode="HTML",
    )
    status = "включены" if p.notifications_enabled else "выключены"
    await callback.answer(f"Уведомления {status}")


# ── Меню редактирования профиля ───────────────────────────────────────────────

@router.callback_query(F.data == "profile:edit_menu")
async def handle_edit_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "Что изменим?",
        reply_markup=profile_edit_v2_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "profile:back")
async def handle_profile_back(
    callback: CallbackQuery,
    user: object,
    container: Container,
) -> None:
    u: User = user  # type: ignore[assignment]
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    if u.profile:
        text = await _build_profile_text(u, container)
        await callback.message.answer(  # type: ignore[union-attr]
            text,
            reply_markup=profile_v2_keyboard(u.profile.notifications_enabled),
            parse_mode="HTML",
        )
    await callback.answer()


# ── Quick FSM: GPA ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "edit:gpa")
async def edit_gpa_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "Введи свой GPA (например: 4.5):",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(ProfileEditStates.editing_gpa)
    await callback.answer()


@router.message(ProfileEditStates.editing_gpa, F.text)
async def edit_gpa_save(
    message: Message, state: FSMContext, user: object, container: Container
) -> None:
    text = (message.text or "").strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu_keyboard())
        return

    u: User = user  # type: ignore[assignment]
    try:
        gpa = float(text.replace(",", "."))
        if not 0 <= gpa <= 5:
            raise ValueError
    except ValueError:
        await message.answer("Введи число от 0 до 5, например: 4.2")
        return

    p = u.profile or UserProfile(user_id=u.id)
    p.gpa = gpa
    p.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(p)
    await state.clear()
    await message.answer(f"✅ GPA сохранён: {gpa}", reply_markup=main_menu_keyboard())


# ── Quick FSM: Язык ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "edit:language")
async def edit_language_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "Укажи уровень английского (например: B2, C1, Fluent):",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(ProfileEditStates.editing_language)
    await callback.answer()


@router.message(ProfileEditStates.editing_language, F.text)
async def edit_language_save(
    message: Message, state: FSMContext, user: object, container: Container
) -> None:
    text = (message.text or "").strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu_keyboard())
        return

    u: User = user  # type: ignore[assignment]
    p = u.profile or UserProfile(user_id=u.id)
    p.language = text[:64]
    p.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(p)
    await state.clear()
    await message.answer(f"✅ Язык сохранён: {text}", reply_markup=main_menu_keyboard())


# ── Quick FSM: Опыт ───────────────────────────────────────────────────────────

@router.callback_query(F.data == "edit:experience")
async def edit_experience_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "Опиши свой опыт (стажировки, проекты, фриланс):",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(ProfileEditStates.editing_experience)
    await callback.answer()


@router.message(ProfileEditStates.editing_experience, F.text)
async def edit_experience_save(
    message: Message, state: FSMContext, user: object, container: Container
) -> None:
    text = (message.text or "").strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu_keyboard())
        return

    u: User = user  # type: ignore[assignment]
    p = u.profile or UserProfile(user_id=u.id)
    p.experience = text[:1000]
    p.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(p)
    await state.clear()
    await message.answer("✅ Опыт сохранён.", reply_markup=main_menu_keyboard())


# ── Quick FSM: Зарплата ───────────────────────────────────────────────────────

@router.callback_query(F.data == "edit:salary")
async def edit_salary_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        "Введи ожидаемую зарплату (число, ₽/мес). Например: 80000:",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(ProfileEditStates.editing_salary)
    await callback.answer()


@router.message(ProfileEditStates.editing_salary, F.text)
async def edit_salary_save(
    message: Message, state: FSMContext, user: object, container: Container
) -> None:
    text = (message.text or "").strip()
    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu_keyboard())
        return

    u: User = user  # type: ignore[assignment]
    try:
        salary = int(text.replace(" ", "").replace(",", ""))
        if salary <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи целое число, например: 80000")
        return

    p = u.profile or UserProfile(user_id=u.id)
    p.expected_salary = salary
    p.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(p)
    await state.clear()
    await message.answer(
        f"✅ Ожидаемая зарплата: {salary:,} ₽".replace(",", " "),
        reply_markup=main_menu_keyboard(),
    )


# ── Waitlist ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "waitlist_menu")
async def handle_waitlist_menu(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(  # type: ignore[union-attr]
        "🚀 <b>Осталось совсем немного…</b>\n\n"
        "Скоро тут будет новый продукт, который\n"
        "поможет тебе найти работу мечты 🎯\n\n"
        "Нажимай кнопку ниже и узнай о нём первым 👇",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 ЛИСТ ОЖИДАНИЯ", callback_data="waitlist_join")],
            [InlineKeyboardButton(text="🔍 ПОДРОБНЕЕ О СТАЖКЕ", url="https://stazhka.ru")],
            [InlineKeyboardButton(text="← Назад", callback_data="waitlist_back_main")],
        ]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "waitlist_join")
async def handle_waitlist_join(
    callback: CallbackQuery,
    user: object,
    container: Container,
) -> None:
    u: User = user  # type: ignore[assignment]
    cache = container.cw_cache

    if cache and await cache.check_waitlist(str(u.id)):
        await callback.answer()
        await callback.message.answer(  # type: ignore[union-attr]
            "Ты уже в списке! 🎉\nМы напишем тебе первым.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Назад", callback_data="waitlist_menu")],
            ]),
        )
        return

    if cache:
        await cache.add_to_waitlist(str(u.id))

    sheets = container.cw_sheets
    if sheets:
        import asyncio as _asyncio
        tg = callback.from_user  # type: ignore[union-attr]
        _asyncio.create_task(
            sheets.append_waitlist(
                user_id=str(u.id),
                telegram_id=tg.id if tg else 0,
                username=tg.username or "" if tg else "",
                first_name=tg.first_name or "" if tg else "",
            )
        )

    await callback.answer()
    await callback.message.answer(  # type: ignore[union-attr]
        "🎉 <b>Поздравляем!</b>\n\n"
        "Теперь ты раньше всех узнаешь о Стажке 🚀",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Главное меню", callback_data="waitlist_back_main")],
        ]),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "waitlist_back_main")
async def handle_waitlist_back_main(callback: CallbackQuery, user: object) -> None:
    u: User = user  # type: ignore[assignment]
    name = u.display_name or ""
    await callback.answer()
    await callback.message.answer(  # type: ignore[union-attr]
        f"Главное меню, {name} 👇",
        reply_markup=main_menu_keyboard(),
    )


# ── Редактирование профиля ────────────────────────────────────────────────────

@router.callback_query(F.data == "edit:specialization")
async def edit_specialization(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        SPEC_TEXT,
        reply_markup=specialization_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.editing_specialization)
    await callback.answer()


@router.callback_query(F.data.startswith("spec:"), OnboardingStates.editing_specialization)
async def save_edited_specialization(
    callback: CallbackQuery, state: FSMContext, user: object, container: Container
) -> None:
    u: User = user  # type: ignore[assignment]
    spec_key = callback.data.split(":")[1]  # type: ignore[union-attr]

    profile = u.profile or UserProfile(user_id=u.id)
    profile.specialty = SPEC_LABELS.get(spec_key, spec_key)
    profile.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(profile)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Специализация обновлена: <b>{profile.specialty}</b>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit:course")
async def edit_course(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        COURSE_TEXT,
        reply_markup=course_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.editing_course)
    await callback.answer()


@router.callback_query(F.data.startswith("course:"), OnboardingStates.editing_course)
async def save_edited_course(
    callback: CallbackQuery, state: FSMContext, user: object, container: Container
) -> None:
    u: User = user  # type: ignore[assignment]
    course_key = callback.data.split(":")[1]  # type: ignore[union-attr]
    course_label = COURSE_LABELS.get(course_key, course_key)

    profile = u.profile or UserProfile(user_id=u.id)
    # Обновляем курс в about
    if profile.about:
        lines = profile.about.splitlines()
        updated = []
        for line in lines:
            if line.startswith("Курс:"):
                updated.append(f"Курс: {course_label}")
            else:
                updated.append(line)
        profile.about = "\n".join(updated)
    profile.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(profile)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Курс обновлён: <b>{course_label}</b>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit:skills")
async def edit_skills(
    callback: CallbackQuery, state: FSMContext, user: object
) -> None:
    u: User = user  # type: ignore[assignment]
    # Текущие навыки из профиля переводим обратно в ключи
    current_labels = u.profile.skills if u.profile else []
    label_to_key = {v: k for k, v in SKILL_LABELS.items()}
    selected = [label_to_key.get(lbl, lbl) for lbl in current_labels]

    await state.update_data(skills=selected)
    await callback.message.answer(  # type: ignore[union-attr]
        SKILLS_TEXT,
        reply_markup=skills_keyboard(selected),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.editing_skills)
    await callback.answer()


@router.callback_query(F.data.startswith("skill:"), OnboardingStates.editing_skills)
async def toggle_skill_edit(callback: CallbackQuery, state: FSMContext) -> None:
    skill_key = callback.data.split(":")[1]  # type: ignore[union-attr]
    fsm_data = await state.get_data()
    selected: list[str] = list(fsm_data.get("skills", []))

    if skill_key in selected:
        selected.remove(skill_key)
    else:
        selected.append(skill_key)

    await state.update_data(skills=selected)
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=skills_keyboard(selected)
    )
    await callback.answer()


@router.callback_query(F.data == "skills:done", OnboardingStates.editing_skills)
async def save_edited_skills(
    callback: CallbackQuery, state: FSMContext, user: object, container: Container
) -> None:
    u: User = user  # type: ignore[assignment]
    fsm_data = await state.get_data()
    selected: list[str] = fsm_data.get("skills", [])

    if not selected:
        await callback.answer("Выбери хотя бы один навык!", show_alert=True)
        return

    profile = u.profile or UserProfile(user_id=u.id)
    profile.skills = [SKILL_LABELS.get(s, s) for s in selected]
    profile.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(profile)

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Навыки обновлены: <b>{', '.join(profile.skills)}</b>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "edit:companies")
async def edit_companies(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer(  # type: ignore[union-attr]
        COMPANIES_TEXT,
        reply_markup=cancel_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(OnboardingStates.editing_companies)
    await callback.answer()


@router.message(OnboardingStates.editing_companies, F.text == "❌ Отмена")
async def cancel_edit_companies(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Редактирование отменено.", reply_markup=main_menu_keyboard())


@router.message(OnboardingStates.editing_companies, F.text)
async def save_edited_companies(
    message: Message,
    state: FSMContext,
    user: object,
    container: Container,
) -> None:
    u: User = user  # type: ignore[assignment]
    companies = message.text or ""

    profile = u.profile or UserProfile(user_id=u.id)
    if profile.about:
        lines = profile.about.splitlines()
        updated = []
        for line in lines:
            if line.startswith("Компании мечты:"):
                updated.append(f"Компании мечты: {companies}")
            else:
                updated.append(line)
        profile.about = "\n".join(updated)
    else:
        profile.about = f"Компании мечты: {companies}"
    profile.updated_at = datetime.utcnow()
    await container.user_repo.upsert_profile(profile)

    await state.clear()
    await message.answer(
        f"✅ Компании обновлены: <b>{companies}</b>",
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(),
    )
