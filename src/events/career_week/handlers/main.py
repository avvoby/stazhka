"""
Главный handler модуля Весенней недели карьеры ВШБ.
Регистрация участника (4 шага) + главное меню недели.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from src.domain.entities.user import User
from src.events.career_week.keyboards.main import (
    DIRECTION_LABELS,
    SKILLS_LIST,
    back_to_cw_keyboard,
    career_week_menu_keyboard,
    courses_keyboard,
    directions_keyboard,
    level_keyboard,
    programs_keyboard,
    skills_keyboard,
)
from src.events.career_week.services.registration import CareerWeekRegistrationService
from src.interface.telegram.keyboards.main import main_menu_keyboard
from src.interface.telegram.middlewares.container import Container

router = Router(name="career_week_main")
_svc = CareerWeekRegistrationService()

# ── FSM States ────────────────────────────────────────────────────────────────

class CareerWeekRegistrationStates(StatesGroup):
    waiting_direction   = State()
    waiting_level       = State()   # бакалавриат / магистратура
    waiting_program     = State()   # выбор или свободный ввод программы
    waiting_course      = State()
    waiting_skills      = State()
    waiting_skill_other = State()   # свободный ввод кастомного навыка


# ── Прогресс-бар ─────────────────────────────────────────────────────────────

_STEPS = ["●○○○○", "●●○○○", "●●●○○", "●●●●○", "●●●●●"]


# ── Точка входа ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "career_week_start")
async def handle_career_week_entry(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    await callback.answer()

    already = await _svc.is_registered(container.session, user.id)
    if already:
        reg = await _svc.get_registration(container.session, user.id)
        await callback.message.answer(  # type: ignore[union-attr]
            f"👋 Ты уже зарегистрирован!\n"
            f"🎫 Твой код участника: <b>{reg.code if reg else '?'}</b>\n\n"
            f"Что хочешь сделать?",
            reply_markup=career_week_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    await state.clear()
    await callback.message.answer(  # type: ignore[union-attr]
        f"<b>Шаг 1 из 5 {_STEPS[0]}</b>\n\n"
        f"Выбери направление обучения:\n\n"
        f"💡 <i>Это поможет нам подобрать для тебя "
        f"подходящие мероприятия и прожарки</i>",
        reply_markup=directions_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(CareerWeekRegistrationStates.waiting_direction)


# ── Шаг 1: Направление ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cw:dir:"), CareerWeekRegistrationStates.waiting_direction)
async def handle_direction(callback: CallbackQuery, state: FSMContext) -> None:
    direction_key = (callback.data or "").split("cw:dir:", 1)[1]
    direction_label = DIRECTION_LABELS.get(direction_key, direction_key)

    await state.update_data(direction=direction_label)
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]

    await callback.message.answer(  # type: ignore[union-attr]
        f"<b>Шаг 2 из 5 {_STEPS[1]}</b>\n\n"
        f"Выбери уровень образования:",
        reply_markup=level_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(CareerWeekRegistrationStates.waiting_level)
    await callback.answer()


# ── Шаг 2: Уровень образования ────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cw:level:"), CareerWeekRegistrationStates.waiting_level)
async def handle_level(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    level = (callback.data or "").split("cw:level:", 1)[1]
    await state.update_data(level=level)
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.answer()

    cache = container.cw_cache
    programs: list[str] = []
    if cache:
        programs = await cache.get_programs_by_level(level)

    if programs:
        await callback.message.answer(  # type: ignore[union-attr]
            f"<b>Шаг 3 из 5 {_STEPS[2]}</b>\n\n"
            f"Выбери свою программу обучения:",
            reply_markup=programs_keyboard(programs),
            parse_mode="HTML",
        )
        await state.set_state(CareerWeekRegistrationStates.waiting_program)
    else:
        await callback.message.answer(  # type: ignore[union-attr]
            f"<b>Шаг 3 из 5 {_STEPS[2]}</b>\n\n"
            f"Список программ ещё не загружен. Напиши свою программу вручную:\n\n"
            f"💡 <i>Например: «Менеджмент», «Финансы и кредит», «Прикладная информатика»</i>",
            parse_mode="HTML",
        )
        await state.set_state(CareerWeekRegistrationStates.waiting_program)


# ── Шаг 3: Программа — выбор из кнопок ───────────────────────────────────────

@router.callback_query(F.data.startswith("cw:prog:"), CareerWeekRegistrationStates.waiting_program)
async def handle_program_select(callback: CallbackQuery, state: FSMContext) -> None:
    value = (callback.data or "").split("cw:prog:", 1)[1]
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.answer()

    if value == "__other__":
        await callback.message.answer(  # type: ignore[union-attr]
            "Напиши свою программу обучения:\n\n"
            "💡 <i>Например: «Менеджмент», «Финансы и кредит»</i>",
            parse_mode="HTML",
        )
        return  # остаёмся в waiting_program, ждём текст

    await state.update_data(program=value)
    await callback.message.answer(  # type: ignore[union-attr]
        f"<b>Шаг 4 из 5 {_STEPS[3]}</b>\n\n"
        f"Какой у тебя курс?",
        reply_markup=courses_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(CareerWeekRegistrationStates.waiting_course)


# ── Шаг 3: Программа — свободный ввод ────────────────────────────────────────

@router.message(CareerWeekRegistrationStates.waiting_program, F.text)
async def handle_program(message: Message, state: FSMContext) -> None:
    program = (message.text or "").strip()
    if not program:
        return

    await state.update_data(program=program)
    await message.answer(
        f"<b>Шаг 4 из 5 {_STEPS[3]}</b>\n\n"
        f"Какой у тебя курс?",
        reply_markup=courses_keyboard(),
        parse_mode="HTML",
    )
    await state.set_state(CareerWeekRegistrationStates.waiting_course)


# ── Шаг 4: Курс ──────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cw:course:"), CareerWeekRegistrationStates.waiting_course)
async def handle_course(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    course = (callback.data or "").split("cw:course:", 1)[1]
    await state.update_data(course=course, skills=[])
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]

    # Навыки из кэша
    cache = container.cw_cache
    skills_list = await cache.get_skills() if cache else []

    await callback.message.answer(  # type: ignore[union-attr]
        f"<b>Шаг 5 из 5 {_STEPS[4]}</b>\n\n"
        f"Выбери свои навыки (можно несколько):",
        reply_markup=skills_keyboard([], skills_list=skills_list),
        parse_mode="HTML",
    )
    await state.set_state(CareerWeekRegistrationStates.waiting_skills)
    await callback.answer()


# ── Шаг 5: Навыки (мультиселект) ─────────────────────────────────────────────

@router.callback_query(F.data.startswith("cw:skill:"), CareerWeekRegistrationStates.waiting_skills)
async def handle_skill_toggle(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    skill = (callback.data or "").split("cw:skill:", 1)[1]

    if skill == "__other__":
        await callback.message.answer(  # type: ignore[union-attr]
            "Введи навык, которого нет в списке:",
        )
        await state.set_state(CareerWeekRegistrationStates.waiting_skill_other)
        await callback.answer()
        return

    fsm = await state.get_data()
    selected: list[str] = list(fsm.get("skills", []))
    if skill in selected:
        selected.remove(skill)
    else:
        selected.append(skill)

    await state.update_data(skills=selected)

    cache = container.cw_cache
    skills_list = await cache.get_skills() if cache else []
    await callback.message.edit_reply_markup(  # type: ignore[union-attr]
        reply_markup=skills_keyboard(selected, skills_list=skills_list)
    )
    await callback.answer()


@router.message(CareerWeekRegistrationStates.waiting_skill_other, F.text)
async def handle_skill_other(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    custom = (message.text or "").strip()
    if not custom:
        await state.set_state(CareerWeekRegistrationStates.waiting_skills)
        return

    fsm = await state.get_data()
    selected: list[str] = list(fsm.get("skills", []))
    if custom not in selected:
        selected.append(custom)
    await state.update_data(skills=selected)

    cache = container.cw_cache
    skills_list = await cache.get_skills() if cache else []
    await message.answer(
        f"✓ Добавлено: «{custom}»\n\nПродолжай выбирать или нажми ✅ Готово.",
        reply_markup=skills_keyboard(selected, skills_list=skills_list),
    )
    await state.set_state(CareerWeekRegistrationStates.waiting_skills)


@router.callback_query(F.data == "cw:skills_done", CareerWeekRegistrationStates.waiting_skills)
async def handle_skills_done(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    fsm = await state.get_data()
    direction: str = fsm.get("direction", "")
    program: str   = fsm.get("program", "")
    course: str    = fsm.get("course", "")
    skills: list[str] = fsm.get("skills", [])

    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.answer()

    try:
        reg = await _svc.register_user(
            session=container.session,
            user_id=user.id,
            direction=direction,
            program=program,
            course=course,
            skills=skills,
        )
    except Exception as e:
        await callback.message.answer(  # type: ignore[union-attr]
            f"Произошла ошибка при регистрации: {e}\nПопробуй ещё раз.",
        )
        await state.clear()
        return

    await state.clear()

    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ <b>Ты зарегистрирован на Весеннюю неделю карьеры ВШБ!</b>\n\n"
        f"🎫 Твой код участника: <b>{reg.code}</b>\n\n"
        f"Сохрани этот код — он понадобится\n"
        f"для получения баллов на мероприятии.\n\n"
        f"Что хочешь сделать?",
        reply_markup=career_week_menu_keyboard(),
        parse_mode="HTML",
    )


# ── Главное меню недели карьеры ───────────────────────────────────────────────

@router.callback_query(F.data == "cw:menu")
async def handle_career_week_menu(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    await callback.answer()

    reg = await _svc.get_registration(container.session, user.id)
    code = reg.code if reg else "—"

    await callback.message.answer(  # type: ignore[union-attr]
        f"🎓 <b>Весенняя неделя карьеры ВШБ</b>\n\n"
        f"Привет, {user.display_name}! Твой код: <b>{code}</b>\n\n"
        f"Что хочешь сделать?",
        reply_markup=career_week_menu_keyboard(),
        parse_mode="HTML",
    )


# ── Навигация из меню недели ──────────────────────────────────────────────────

@router.callback_query(F.data == "cw:exit")
async def handle_cw_exit(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)  # type: ignore[union-attr]
    await callback.message.answer(  # type: ignore[union-attr]
        "Возвращаемся в Стажку 👇",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


# cw:my_bookings обрабатывается в roasts.py
