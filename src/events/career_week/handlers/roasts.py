"""
Хендлеры: Запись на прожарки Весенней недели карьеры.
"""
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from src.domain.entities.user import User
from src.events.career_week.models import RoastSlot
from src.interface.telegram.middlewares.container import Container
from src.interface.telegram.states.forms import RoastBookingStates

logger = logging.getLogger(__name__)

router = Router(name="career_week_roasts")

_TYPE_LABELS = {
    "resume":     "📄 Прожарка резюме",
    "interview":  "🎤 Прожарка собеседования",
    "fast_track": "⚡ Быстрый отбор на вакансию",
}


# ── Клавиатуры ───────────────────────────────────────────────────────────────

def _type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📄 Прожарка резюме",           callback_data="cw:roast_type:resume")],
            [InlineKeyboardButton(text="🎤 Прожарка собеседования",     callback_data="cw:roast_type:interview")],
            [InlineKeyboardButton(text="⚡ Быстрый отбор на вакансию",  callback_data="cw:roast_type:fast_track")],
            [InlineKeyboardButton(text="← Назад",                       callback_data="cw:menu")],
        ]
    )


def _slots_keyboard(slots: list[RoastSlot]) -> InlineKeyboardMarkup:
    rows = []
    for slot in slots:
        if slot.type == "fast_track" and slot.company:
            label = f"⚡ {slot.company} · {slot.date}, {slot.time} · {slot.direction}"
        else:
            label = f"📅 {slot.date}, {slot.time} · {slot.direction}"
        if slot.is_available:
            text = f"{label} · {slot.available_seats} места"
            cb = f"cw:slot:{slot.id}"
        else:
            text = f"❌ {label} · мест нет"
            cb = "cw:slot_full"
        rows.append([InlineKeyboardButton(text=text, callback_data=cb)])
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="cw:roasts")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _resume_upload_keyboard_mandatory() -> InlineKeyboardMarkup:
    """Клавиатура для fast_track — без кнопки Пропустить."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📎 Загрузить PDF",   callback_data="cw:roast_resume_hint")],
            [InlineKeyboardButton(text="🖼 Загрузить фото",  callback_data="cw:roast_resume_hint")],
            [InlineKeyboardButton(text="🔗 Вставить ссылку", callback_data="cw:roast_resume_hint")],
        ]
    )


def _resume_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📎 Загрузить PDF",   callback_data="cw:roast_skip")],  # placeholder — file comes via message
            [InlineKeyboardButton(text="🔗 Вставить ссылку", callback_data="cw:roast_skip")],   # placeholder
            [InlineKeyboardButton(text="Пропустить →",       callback_data="cw:roast_skip")],
        ]
    )


def _resume_upload_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить →", callback_data="cw:roast_skip")],
        ]
    )


def _after_booking_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Мои записи",          callback_data="cw:my_bookings")],
            [InlineKeyboardButton(text="← Главное меню недели",  callback_data="cw:menu")],
        ]
    )


def _cancel_confirm_keyboard(booking_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, отменить",  callback_data=f"cw:confirm_cancel:{booking_id}"),
                InlineKeyboardButton(text="← Нет, оставить", callback_data="cw:my_bookings"),
            ]
        ]
    )


def _after_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Записаться снова",   callback_data="cw:roasts")],
            [InlineKeyboardButton(text="← Главное меню недели", callback_data="cw:menu")],
        ]
    )


# ── Меню прожарок ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:roasts")
async def handle_roasts_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(  # type: ignore[union-attr]
        "🔥 <b>Запись на прожарку</b>\n\nВыбери формат:",
        reply_markup=_type_keyboard(),
        parse_mode="HTML",
    )


# ── Выбор типа прожарки ───────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cw:roast_type:"))
async def handle_roast_type(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    slot_type = (callback.data or "").split("cw:roast_type:", 1)[1]
    type_label = _TYPE_LABELS.get(slot_type, slot_type)

    cache = container.cw_cache
    all_slots = await cache.get_roast_slots() if cache else []
    slots = sorted(
        [s for s in all_slots if s.type == slot_type],
        key=lambda s: (s.date, s.time),
    )

    if not slots:
        await callback.message.answer(  # type: ignore[union-attr]
            "Свободных мест пока нет 😔\nПопробуй позже или следи за обновлениями.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="cw:roasts")]]
            ),
        )
        return

    await state.update_data(slot_type=slot_type)
    await state.set_state(RoastBookingStates.choosing_slot)

    if slot_type == "fast_track":
        header = f"<b>{type_label}</b>\n⚠️ Резюме обязательно.\n\nВыбери вакансию:"
    else:
        header = f"<b>{type_label}</b>\nВыбери удобный слот:"

    await callback.message.answer(  # type: ignore[union-attr]
        header,
        reply_markup=_slots_keyboard(slots),
        parse_mode="HTML",
    )


# ── Занятый слот ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:slot_full")
async def handle_slot_full(callback: CallbackQuery) -> None:
    await callback.answer("На этот слот мест нет", show_alert=False)


# ── Выбор слота ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cw:slot:"), RoastBookingStates.choosing_slot)
async def handle_slot_select(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    slot_id = (callback.data or "").split("cw:slot:", 1)[1]

    cache = container.cw_cache
    all_slots = await cache.get_roast_slots() if cache else []
    slot = next((s for s in all_slots if s.id == slot_id), None)

    if not slot or not slot.is_available:
        await callback.message.answer(  # type: ignore[union-attr]
            "Упс, только что заняли последнее место 😔\nВыбери другой слот.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="cw:roasts")]]
            ),
        )
        await state.clear()
        return

    is_fast_track = slot.type == "fast_track"
    await state.update_data(
        slot_id=slot_id,
        slot_date=slot.date,
        slot_time=slot.time,
        slot_direction=slot.direction,
        slot_company=slot.company or "",
        is_fast_track=is_fast_track,
    )
    await state.set_state(RoastBookingStates.uploading_resume)

    if is_fast_track:
        company_label = slot.company or slot.direction
        await callback.message.answer(  # type: ignore[union-attr]
            f"⚡ <b>Быстрый отбор на вакансию — {company_label}</b>\n\n"
            f"Для участия необходимо загрузить резюме.\n"
            f"Без резюме запись невозможна.\n\n"
            f"Загрузи резюме:",
            reply_markup=_resume_upload_keyboard_mandatory(),
            parse_mode="HTML",
        )
    else:
        await callback.message.answer(  # type: ignore[union-attr]
            f"📅 <b>{slot.date}, {slot.time}</b>\n"
            f"🎯 Направление: {slot.direction}\n\n"
            f"Загрузи своё резюме — это поможет провести более предметную прожарку.\n\n"
            f"<i>Отправь PDF-файл, фото или вставь ссылку. "
            f"Или нажми «Пропустить», если резюме нет.</i>",
            reply_markup=_resume_upload_keyboard(),
            parse_mode="HTML",
        )


# ── Загрузка резюме — файл ────────────────────────────────────────────────────

@router.message(RoastBookingStates.uploading_resume, F.document)
async def handle_resume_file(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    doc = message.document
    if not doc:
        return
    if doc.mime_type != "application/pdf":
        await message.answer("Пожалуйста, загрузи файл в формате PDF.")
        return
    await _complete_booking(message, state, user, container, resume_file_id=doc.file_id)


@router.message(RoastBookingStates.uploading_resume, F.photo)
async def handle_resume_photo(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    photos = message.photo
    if not photos:
        return
    largest = max(photos, key=lambda p: p.file_size or 0)
    await _complete_booking(message, state, user, container, resume_file_id=largest.file_id)


# ── Загрузка резюме — ссылка ──────────────────────────────────────────────────

@router.message(RoastBookingStates.uploading_resume, F.text)
async def handle_resume_link(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    text = (message.text or "").strip()
    if not text.startswith("http"):
        fsm_data = await state.get_data()
        if fsm_data.get("is_fast_track"):
            await message.answer(
                "Для быстрого отбора резюме обязательно.\n"
                "Загрузи файл или вставь ссылку.",
                reply_markup=_resume_upload_keyboard_mandatory(),
            )
        else:
            await message.answer(
                "Пожалуйста, отправь корректную ссылку (начинается с http...) "
                "или нажми «Пропустить»."
            )
        return
    await _complete_booking(message, state, user, container, resume_url=text)


# ── Подсказка для fast_track (информационные кнопки) ─────────────────────────

@router.callback_query(F.data == "cw:roast_resume_hint")
async def handle_resume_hint(callback: CallbackQuery) -> None:
    await callback.answer("Отправь файл или ссылку прямо в чат", show_alert=False)


# ── Пропустить резюме ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:roast_skip", RoastBookingStates.uploading_resume)
async def handle_resume_skip(
    callback: CallbackQuery,
    state: FSMContext,
    user: User,
    container: Container,
) -> None:
    fsm_data = await state.get_data()
    if fsm_data.get("is_fast_track"):
        await callback.answer(
            "Для быстрого отбора резюме обязательно.",
            show_alert=True,
        )
        return
    await callback.answer()
    await _complete_booking(callback.message, state, user, container)  # type: ignore[arg-type]


# ── Завершение бронирования ───────────────────────────────────────────────────

async def _complete_booking(
    message: Message,
    state: FSMContext,
    user: User,
    container: Container,
    resume_file_id: str | None = None,
    resume_url: str | None = None,
) -> None:
    fsm = await state.get_data()
    slot_id: str = fsm.get("slot_id", "")
    slot_type: str = fsm.get("slot_type", "")
    slot_date: str = fsm.get("slot_date", "")
    slot_time: str = fsm.get("slot_time", "")
    slot_direction: str = fsm.get("slot_direction", "")

    await state.clear()

    reg_svc = container.cw_registration
    if reg_svc is None:
        from src.events.career_week.services.registration import CareerWeekRegistrationService
        reg_svc = CareerWeekRegistrationService()

    try:
        booking = await reg_svc.book_roast(
            session=container.session,
            user_id=user.id,
            slot_id=slot_id,
            slot_type=slot_type,
            direction=slot_direction,
            resume_file_id=resume_file_id,
            resume_url=resume_url,
        )
    except ValueError as e:
        await message.answer(
            f"😔 {e}\n\nВыбери другой слот.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← К слотам", callback_data="cw:roasts")]]
            ),
        )
        return
    except Exception:
        logger.exception("Ошибка бронирования слота %s", slot_id)
        await message.answer("Произошла ошибка. Попробуй ещё раз.")
        return

    # Получаем код участника
    reg = await reg_svc.get_registration(container.session, user.id)
    user_code = reg.code if reg else "—"

    # Синхронизируем в Sheets (в фоне — не блокируем ответ)
    sheets = container.cw_sheets
    if sheets:
        import asyncio
        asyncio.create_task(
            sheets.append_roast_booking(booking, user_code)
        )

    type_label = _TYPE_LABELS.get(slot_type, slot_type)
    await message.answer(
        f"✅ <b>Ты записан!</b>\n\n"
        f"🔥 {type_label} — {slot_direction}\n"
        f"📅 {slot_date}, {slot_time}\n"
        f"🎫 Твой код: <b>{user_code}</b>\n\n"
        f"Все свои записи можешь посмотреть\n"
        f"в разделе «Мои записи» — там же\n"
        f"можно отменить запись.",
        reply_markup=_after_booking_keyboard(),
        parse_mode="HTML",
    )


# ── Мои записи ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:my_bookings")
async def handle_my_bookings(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    await callback.answer()

    reg_svc = container.cw_registration
    if reg_svc is None:
        from src.events.career_week.services.registration import CareerWeekRegistrationService
        reg_svc = CareerWeekRegistrationService()

    bookings = await reg_svc.get_user_bookings(container.session, user.id)

    if not bookings:
        await callback.message.answer(  # type: ignore[union-attr]
            "📝 <b>Мои записи</b>\n\nУ тебя пока нет записей на прожарки.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔥 Записаться на прожарку", callback_data="cw:roasts")],
                    [InlineKeyboardButton(text="← Назад",                   callback_data="cw:menu")],
                ]
            ),
            parse_mode="HTML",
        )
        return

    lines = []
    cancel_buttons: list[list[InlineKeyboardButton]] = []
    for i, b in enumerate(bookings, 1):
        type_label = _TYPE_LABELS.get(b.slot_type, b.slot_type)
        lines.append(f"{i}. {type_label} — {b.direction}\n   📅 слот {b.slot_id}")
        cancel_buttons.append([
            InlineKeyboardButton(
                text=f"❌ Отменить запись {i}",
                callback_data=f"cw:cancel_booking:{b.id}",
            )
        ])

    cancel_buttons.append([InlineKeyboardButton(text="← Назад", callback_data="cw:menu")])

    await callback.message.answer(  # type: ignore[union-attr]
        f"📝 <b>Мои записи ({len(bookings)}):</b>\n\n" + "\n\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=cancel_buttons),
        parse_mode="HTML",
    )


# ── Отмена записи ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("cw:cancel_booking:"))
async def handle_cancel_booking(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    await callback.answer()
    booking_id_str = (callback.data or "").split("cw:cancel_booking:", 1)[1]

    reg_svc = container.cw_registration
    if reg_svc is None:
        from src.events.career_week.services.registration import CareerWeekRegistrationService
        reg_svc = CareerWeekRegistrationService()

    bookings = await reg_svc.get_user_bookings(container.session, user.id)
    booking = next((b for b in bookings if str(b.id) == booking_id_str), None)

    if not booking:
        await callback.message.answer("Запись не найдена.")  # type: ignore[union-attr]
        return

    type_label = _TYPE_LABELS.get(booking.slot_type, booking.slot_type)
    await callback.message.answer(  # type: ignore[union-attr]
        f"Отменить запись?\n"
        f"🔥 {type_label} — {booking.direction}\n"
        f"📅 слот {booking.slot_id}",
        reply_markup=_cancel_confirm_keyboard(booking_id_str),
    )


@router.callback_query(F.data.startswith("cw:confirm_cancel:"))
async def handle_confirm_cancel(
    callback: CallbackQuery,
    user: User,
    container: Container,
) -> None:
    await callback.answer()
    booking_id_str = (callback.data or "").split("cw:confirm_cancel:", 1)[1]

    from uuid import UUID
    try:
        booking_uuid = UUID(booking_id_str)
    except ValueError:
        await callback.message.answer("Некорректный идентификатор записи.")  # type: ignore[union-attr]
        return

    reg_svc = container.cw_registration
    if reg_svc is None:
        from src.events.career_week.services.registration import CareerWeekRegistrationService
        reg_svc = CareerWeekRegistrationService()

    cancelled = await reg_svc.cancel_booking(
        session=container.session,
        booking_id=booking_uuid,
        user_id=user.id,
    )

    if not cancelled:
        await callback.message.answer(  # type: ignore[union-attr]
            "Не удалось отменить запись. Возможно, она уже была отменена.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="cw:my_bookings")]]
            ),
        )
        return

    # Обновляем Sheets в фоне
    sheets = container.cw_sheets
    if sheets:
        import asyncio
        asyncio.create_task(
            sheets.update_roast_cancellation(booking_id_str)
        )

    await callback.message.answer(  # type: ignore[union-attr]
        "✅ <b>Запись отменена.</b>\nМесто освободилось для других участников.",
        reply_markup=_after_cancel_keyboard(),
        parse_mode="HTML",
    )
