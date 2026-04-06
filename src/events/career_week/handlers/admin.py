"""
Админ-панель Весенней недели карьеры ВШБ.
"""
import asyncio
import logging
from datetime import datetime
from functools import wraps
from typing import Any, Callable

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import text

from src.events.career_week.config import career_week_settings
from src.interface.telegram.middlewares.container import Container
from src.interface.telegram.states.forms import BroadcastStates

logger = logging.getLogger(__name__)

router = Router(name="career_week_admin")

_SUPERADMIN = 5645685337

# ── Декоратор проверки прав ───────────────────────────────────────────────────

def cw_admin_only(func: Callable) -> Callable:
    """Проверяет, является ли пользователь CW-администратором."""
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Ищем объект с from_user среди args
        event = args[0] if args else None
        container: Container | None = kwargs.get("container")

        from_user = None
        if hasattr(event, "from_user"):
            from_user = event.from_user
        elif hasattr(event, "message") and event.message:
            from_user = event.message.from_user

        if from_user is None:
            return None

        tg_id = from_user.id
        cache = container.cw_cache if container else None
        is_admin = tg_id in career_week_settings.career_week_admin_ids
        if not is_admin and cache:
            is_admin = await cache.is_admin(tg_id)

        if not is_admin:
            if isinstance(event, CallbackQuery):
                await event.answer("⛔ Доступ запрещён", show_alert=True)
            elif isinstance(event, Message):
                await event.answer("⛔ Доступ запрещён")
            return None

        return await func(*args, **kwargs)
    return wrapper


# ── Клавиатуры ────────────────────────────────────────────────────────────────

def _admin_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Рассылка",              callback_data="cw:admin:broadcast")],
            [InlineKeyboardButton(text="🔄 Обновить контент",       callback_data="cw:admin:update")],
            [InlineKeyboardButton(text="👥 Управление админами",    callback_data="cw:admin:admins")],
            [InlineKeyboardButton(text="📊 Статистика",             callback_data="cw:admin:stats")],
        ]
    )


def _audience_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Всем участникам",           callback_data="cw:admin:audience:all")],
            [InlineKeyboardButton(text="🎯 По направлению обучения",   callback_data="cw:admin:audience:direction")],
            [InlineKeyboardButton(text="🎯 По курсу",                  callback_data="cw:admin:audience:course")],
            [InlineKeyboardButton(text="📋 По списку Telegram ID",     callback_data="cw:admin:audience:list")],
            [InlineKeyboardButton(text="← Назад",                      callback_data="cw:admin:menu")],
        ]
    )


def _directions_audience_keyboard() -> InlineKeyboardMarkup:
    from src.events.career_week.keyboards.main import DIRECTIONS
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"cw:admin:audience:dir_val:{key}")]
        for label, key in DIRECTIONS
    ]
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="cw:admin:broadcast")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _courses_audience_keyboard() -> InlineKeyboardMarkup:
    from src.events.career_week.keyboards.main import COURSES
    rows = [
        [InlineKeyboardButton(text=c, callback_data=f"cw:admin:audience:course_val:{c}")]
        for c in COURSES
    ]
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="cw:admin:broadcast")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _add_button_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить кнопку", callback_data="cw:admin:add_button")],
            [InlineKeyboardButton(text="Пропустить →",       callback_data="cw:admin:skip_buttons")],
        ]
    )


def _more_button_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ещё кнопку", callback_data="cw:admin:add_button")],
            [InlineKeyboardButton(text="Готово →",      callback_data="cw:admin:skip_buttons")],
        ]
    )


def _attach_file_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить →", callback_data="cw:admin:skip_file")],
        ]
    )


def _confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить",      callback_data="cw:admin:send_broadcast"),
                InlineKeyboardButton(text="✏️ Изменить текст", callback_data="cw:admin:edit_text"),
            ],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cw:admin:cancel_broadcast")],
        ]
    )


def _back_to_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← Назад в меню", callback_data="cw:admin:menu")]]
    )


# ── Главное меню ─────────────────────────────────────────────────────────────

@router.message(Command("cwadmin"))
@cw_admin_only
async def handle_admin_menu_cmd(message: Message, container: Container) -> None:
    await message.answer(
        "⚙️ <b>Админ-панель</b>\nВесенняя неделя карьеры ВШБ\n\nВыбери действие:",
        reply_markup=_admin_menu_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cw:admin:menu")
@cw_admin_only
async def handle_admin_menu(callback: CallbackQuery, container: Container) -> None:
    await callback.answer()
    await callback.message.answer(  # type: ignore[union-attr]
        "⚙️ <b>Админ-панель</b>\nВесенняя неделя карьеры ВШБ\n\nВыбери действие:",
        reply_markup=_admin_menu_keyboard(),
        parse_mode="HTML",
    )


# ── Рассылка ─────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:admin:broadcast")
@cw_admin_only
async def handle_broadcast_start(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    await state.clear()
    await state.set_state(BroadcastStates.choosing_audience)
    await callback.message.answer(  # type: ignore[union-attr]
        "Кому отправить?",
        reply_markup=_audience_keyboard(),
    )


@router.callback_query(F.data.startswith("cw:admin:audience:"), BroadcastStates.choosing_audience)
@cw_admin_only
async def handle_broadcast_audience(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    suffix = (callback.data or "").split("cw:admin:audience:", 1)[1]

    if suffix == "all":
        await state.update_data(audience="all", audience_filter=None)
        await _ask_broadcast_text(callback.message, state)  # type: ignore[arg-type]

    elif suffix == "direction":
        await callback.message.answer(  # type: ignore[union-attr]
            "Выбери направление:",
            reply_markup=_directions_audience_keyboard(),
        )

    elif suffix == "course":
        await callback.message.answer(  # type: ignore[union-attr]
            "Выбери курс:",
            reply_markup=_courses_audience_keyboard(),
        )

    elif suffix == "list":
        await state.update_data(audience="list")
        await state.set_state(BroadcastStates.entering_filter)
        await callback.message.answer(  # type: ignore[union-attr]
            "Отправь список Telegram ID — по одному на строку или через запятую.\n"
            "Можно загрузить .txt файл.",
        )

    elif suffix.startswith("dir_val:"):
        direction = suffix.split("dir_val:", 1)[1]
        await state.update_data(audience="direction", audience_filter=direction)
        await _ask_broadcast_text(callback.message, state)  # type: ignore[arg-type]

    elif suffix.startswith("course_val:"):
        course = suffix.split("course_val:", 1)[1]
        await state.update_data(audience="course", audience_filter=course)
        await _ask_broadcast_text(callback.message, state)  # type: ignore[arg-type]


@router.message(BroadcastStates.entering_filter, F.text)
@cw_admin_only
async def handle_broadcast_filter_text(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    raw = message.text or ""
    ids = _parse_ids(raw)
    if not ids:
        await message.answer("Не нашёл ни одного числового ID. Попробуй ещё раз.")
        return
    await state.update_data(audience_filter=ids)
    await _ask_broadcast_text(message, state)


@router.message(BroadcastStates.entering_filter, F.document)
@cw_admin_only
async def handle_broadcast_filter_file(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    doc = message.document
    if not doc:
        return
    import io
    bot = message.bot
    assert bot is not None
    file = await bot.get_file(doc.file_id)
    buf = io.BytesIO()
    await bot.download_file(file.file_path, buf)  # type: ignore[arg-type]
    content = buf.getvalue().decode("utf-8", errors="ignore")
    ids = _parse_ids(content)
    if not ids:
        await message.answer("Не нашёл ни одного числового ID в файле.")
        return
    await state.update_data(audience_filter=ids)
    await _ask_broadcast_text(message, state)


async def _ask_broadcast_text(message: Message, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.entering_text)
    await message.answer(
        "Напиши текст сообщения.\n\n"
        "Поддерживается форматирование Telegram:\n"
        "<code>*жирный* _курсив_ `код`</code>",
        parse_mode="HTML",
    )


@router.message(BroadcastStates.entering_text, F.text)
@cw_admin_only
async def handle_broadcast_text_input(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    await state.update_data(broadcast_text=message.text, buttons=[])
    await message.answer(
        "Добавить кнопки к сообщению?",
        reply_markup=_add_button_keyboard(),
    )


@router.callback_query(F.data == "cw:admin:add_button")
@cw_admin_only
async def handle_add_button_start(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    await state.set_state(BroadcastStates.adding_button_text)
    await callback.message.answer("Напиши текст кнопки:")  # type: ignore[union-attr]


@router.message(BroadcastStates.adding_button_text, F.text)
@cw_admin_only
async def handle_button_text(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    await state.update_data(pending_button_text=message.text)
    await state.set_state(BroadcastStates.adding_button_url)
    await message.answer("Напиши URL кнопки:")


@router.message(BroadcastStates.adding_button_url, F.text)
@cw_admin_only
async def handle_button_url(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    url = (message.text or "").strip()
    fsm = await state.get_data()
    buttons: list[dict] = list(fsm.get("buttons", []))
    buttons.append({"text": fsm.get("pending_button_text", ""), "url": url})
    await state.update_data(buttons=buttons, pending_button_text=None)
    await message.answer(
        f"✓ Кнопка добавлена. Всего кнопок: {len(buttons)}\nДобавить ещё?",
        reply_markup=_more_button_keyboard(),
    )


@router.callback_query(F.data == "cw:admin:skip_buttons")
@cw_admin_only
async def handle_skip_buttons(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    await state.set_state(BroadcastStates.uploading_file)
    await callback.message.answer(  # type: ignore[union-attr]
        "Прикрепить файл к рассылке?",
        reply_markup=_attach_file_keyboard(),
    )


@router.message(BroadcastStates.uploading_file, F.document | F.photo)
@cw_admin_only
async def handle_broadcast_file(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    if message.document:
        await state.update_data(file_id=message.document.file_id, file_type="document")
    elif message.photo:
        largest = max(message.photo, key=lambda p: p.file_size or 0)
        await state.update_data(file_id=largest.file_id, file_type="photo")
    await _show_broadcast_preview(message, state, container)


@router.callback_query(F.data == "cw:admin:skip_file")
@cw_admin_only
async def handle_skip_file(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    await state.update_data(file_id=None, file_type=None)
    await _show_broadcast_preview(callback.message, state, container)  # type: ignore[arg-type]


async def _show_broadcast_preview(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    fsm = await state.get_data()
    text = fsm.get("broadcast_text", "")
    buttons: list[dict] = fsm.get("buttons", [])

    # Считаем получателей
    count = await _count_recipients(container, fsm)

    buttons_preview = ""
    if buttons:
        buttons_preview = "\n" + " | ".join(f"[{b['text']}]" for b in buttons)

    preview = (
        f"Превью рассылки:\n"
        f"─────────────\n"
        f"{text}{buttons_preview}\n"
        f"─────────────\n"
        f"Получателей: <b>{count}</b> человек\n\n"
        f"Отправить?"
    )
    await state.set_state(BroadcastStates.confirming)
    await message.answer(preview, reply_markup=_confirm_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "cw:admin:edit_text", BroadcastStates.confirming)
@cw_admin_only
async def handle_edit_text(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    await state.set_state(BroadcastStates.entering_text)
    await callback.message.answer("Напиши новый текст сообщения:")  # type: ignore[union-attr]


@router.callback_query(F.data == "cw:admin:cancel_broadcast")
@cw_admin_only
async def handle_cancel_broadcast(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    await state.clear()
    await callback.message.answer(  # type: ignore[union-attr]
        "Рассылка отменена.",
        reply_markup=_back_to_admin_keyboard(),
    )


@router.callback_query(F.data == "cw:admin:send_broadcast", BroadcastStates.confirming)
@cw_admin_only
async def handle_broadcast_send(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    fsm = await state.get_data()
    await state.clear()

    text = fsm.get("broadcast_text", "")
    buttons: list[dict] = fsm.get("buttons", [])
    file_id: str | None = fsm.get("file_id")
    file_type: str | None = fsm.get("file_type")

    user_ids = await _get_recipient_ids(container, fsm)
    total = len(user_ids)

    # Строим reply_markup из кнопок
    reply_markup = None
    if buttons:
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=b["text"], url=b["url"])] for b in buttons]
        )

    bot = callback.bot
    assert bot is not None

    progress_msg = await callback.message.answer(  # type: ignore[union-attr]
        f"📤 Отправляю... 0/{total}",
    )

    sent = 0
    errors = 0
    for i, tg_id in enumerate(user_ids):
        try:
            if file_id and file_type == "photo":
                await bot.send_photo(tg_id, photo=file_id, caption=text,
                                     reply_markup=reply_markup, parse_mode="Markdown")
            elif file_id and file_type == "document":
                await bot.send_document(tg_id, document=file_id, caption=text,
                                        reply_markup=reply_markup, parse_mode="Markdown")
            else:
                await bot.send_message(tg_id, text,
                                       reply_markup=reply_markup, parse_mode="Markdown")
            sent += 1
        except Exception:
            errors += 1

        if (i + 1) % 20 == 0:
            try:
                await progress_msg.edit_text(f"📤 Отправляю... {i + 1}/{total}")
            except Exception:
                pass

        await asyncio.sleep(0.05)

    await progress_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"Отправлено: {sent}\n"
        f"Ошибок: {errors}",
        parse_mode="HTML",
    )


# ── Обновить контент ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:admin:update")
@cw_admin_only
async def handle_update_content(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    msg = await callback.message.answer("🔄 Читаю Google Таблицу... ⏳")  # type: ignore[union-attr]

    sheets = container.cw_sheets
    cache = container.cw_cache

    if not sheets or not cache:
        await msg.edit_text(
            "❌ Google Sheets не настроен. Проверь GOOGLE_SERVICE_ACCOUNT_JSON.",
            reply_markup=_back_to_admin_keyboard(),
        )
        return

    try:
        stats = await cache.sync_from_sheets(sheets)
    except Exception as e:
        logger.exception("Ошибка синхронизации контента")
        await msg.edit_text(
            f"❌ Ошибка синхронизации: {e}",
            reply_markup=_back_to_admin_keyboard(),
        )
        return

    await msg.edit_text(
        f"✅ <b>Контент обновлён!</b>\n\n"
        f"• Партнёры: {stats.get('partners', 0)} компаний\n"
        f"• Мероприятия: {stats.get('schedule', 0)} событий\n"
        f"• Слоты прожарок: {stats.get('roast_slots', 0)} слотов\n"
        f"• Программы обучения: {stats.get('programs', 0)} программ\n\n"
        f"Пользователи видят новые данные.",
        reply_markup=_back_to_admin_keyboard(),
        parse_mode="HTML",
    )


# ── Управление админами ───────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:admin:admins")
@cw_admin_only
async def handle_admin_management(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    cache = container.cw_cache
    admins = await cache.get_admins() if cache else []

    lines = "\n".join(f"• {tid}" for tid in admins) if admins else "— список пуст —"
    rows: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="cw:admin:add_admin")],
        [InlineKeyboardButton(text="➖ Удалить админа",  callback_data="cw:admin:remove_admin")],
        [InlineKeyboardButton(text="← Назад",            callback_data="cw:admin:menu")],
    ]
    await callback.message.answer(  # type: ignore[union-attr]
        f"👥 <b>Администраторы:</b>\n{lines}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cw:admin:add_admin")
@cw_admin_only
async def handle_add_admin_start(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    await callback.answer()
    await state.set_state("cw_admin:waiting_forward")
    await callback.message.answer(  # type: ignore[union-attr]
        "Перешли мне любое сообщение от нового администратора:",
    )


@router.message(F.forward_from, lambda msg, **_: True)
async def handle_add_admin_forward(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    current = await state.get_state()
    if current != "cw_admin:waiting_forward":
        return

    # Проверяем права
    tg_id = message.from_user.id if message.from_user else 0
    cache = container.cw_cache
    is_admin = tg_id in career_week_settings.career_week_admin_ids
    if not is_admin and cache:
        is_admin = await cache.is_admin(tg_id)
    if not is_admin:
        return

    forward_from = message.forward_from
    if not forward_from:
        await message.answer("Не могу определить Telegram ID. Убедись, что пользователь не скрыл профиль.")
        return

    new_id = forward_from.id
    sheets = container.cw_sheets
    if sheets:
        admins = await cache.get_admins() if cache else []
        if new_id not in admins:
            admins.append(new_id)
            try:
                await sheets.update_admins(admins)
                if cache:
                    import json
                    from src.events.career_week.services.cache import _PREFIX, _TTL
                    await cache._redis.setex(_PREFIX + "admins", _TTL, json.dumps(admins))
            except Exception:
                logger.exception("Ошибка добавления админа")
                await message.answer("Ошибка сохранения. Попробуй снова.")
                await state.clear()
                return

    await state.clear()
    await message.answer(
        f"✅ Добавлен администратор <b>{new_id}</b>",
        parse_mode="HTML",
        reply_markup=_back_to_admin_keyboard(),
    )


@router.callback_query(F.data == "cw:admin:remove_admin")
@cw_admin_only
async def handle_remove_admin(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    cache = container.cw_cache
    admins = await cache.get_admins() if cache else []

    from_id = callback.from_user.id if callback.from_user else 0
    rows = []
    for tid in admins:
        if tid == _SUPERADMIN or tid == from_id:
            continue
        rows.append([InlineKeyboardButton(
            text=f"🗑 {tid}",
            callback_data=f"cw:admin:do_remove:{tid}",
        )])
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="cw:admin:admins")])

    await callback.message.answer(  # type: ignore[union-attr]
        "Выбери администратора для удаления:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


@router.callback_query(F.data.startswith("cw:admin:do_remove:"))
@cw_admin_only
async def handle_do_remove_admin(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    target_id = int((callback.data or "").split("cw:admin:do_remove:", 1)[1])
    from_id = callback.from_user.id if callback.from_user else 0

    if target_id == _SUPERADMIN or target_id == from_id:
        await callback.answer("Нельзя удалить этого администратора", show_alert=True)
        return

    cache = container.cw_cache
    sheets = container.cw_sheets
    admins = await cache.get_admins() if cache else []
    admins = [a for a in admins if a != target_id]

    if sheets:
        try:
            await sheets.update_admins(admins)
            if cache:
                import json
                from src.events.career_week.services.cache import _PREFIX, _TTL
                await cache._redis.setex(_PREFIX + "admins", _TTL, json.dumps(admins))
        except Exception:
            logger.exception("Ошибка удаления админа")
            await callback.message.answer("Ошибка сохранения.")  # type: ignore[union-attr]
            return

    await callback.message.answer(  # type: ignore[union-attr]
        f"✅ Администратор <b>{target_id}</b> удалён.",
        parse_mode="HTML",
        reply_markup=_back_to_admin_keyboard(),
    )


# ── Статистика ────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "cw:admin:stats")
@cw_admin_only
async def handle_stats(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    session = container.session

    total_row = await session.execute(
        text("SELECT COUNT(*) FROM career_week_registrations")
    )
    total: int = total_row.scalar() or 0

    dir_rows = await session.execute(
        text("SELECT direction, COUNT(*) as cnt FROM career_week_registrations GROUP BY direction ORDER BY cnt DESC")
    )
    by_direction = dir_rows.fetchall()

    course_rows = await session.execute(
        text("SELECT course, COUNT(*) as cnt FROM career_week_registrations GROUP BY course ORDER BY cnt DESC")
    )
    by_course = course_rows.fetchall()

    roast_resume_row = await session.execute(
        text("SELECT COUNT(*) FROM career_week_roast_bookings WHERE slot_type = 'resume' AND cancelled_at IS NULL")
    )
    roast_resume: int = roast_resume_row.scalar() or 0

    roast_interview_row = await session.execute(
        text("SELECT COUNT(*) FROM career_week_roast_bookings WHERE slot_type = 'interview' AND cancelled_at IS NULL")
    )
    roast_interview: int = roast_interview_row.scalar() or 0

    dir_lines = "\n".join(f"  • {r.direction}: {r.cnt}" for r in by_direction) or "  — нет данных"
    course_lines = "\n".join(f"  • {r.course}: {r.cnt}" for r in by_course) or "  — нет данных"
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")

    await callback.message.answer(  # type: ignore[union-attr]
        f"📊 <b>Статистика на {now_str}</b>\n\n"
        f"👥 Зарегистрировано: <b>{total}</b> человек\n\n"
        f"По направлениям:\n{dir_lines}\n\n"
        f"По курсам:\n{course_lines}\n\n"
        f"🔥 Записей на прожарку резюме: <b>{roast_resume}</b>\n"
        f"🎤 Записей на прожарку собеседований: <b>{roast_interview}</b>",
        reply_markup=_back_to_admin_keyboard(),
        parse_mode="HTML",
    )


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _parse_ids(raw: str) -> list[int]:
    result = []
    for token in raw.replace(",", "\n").split():
        token = token.strip()
        if token.isdigit():
            result.append(int(token))
    return result


async def _count_recipients(container: Container, fsm: dict) -> int:
    audience = fsm.get("audience", "all")
    audience_filter = fsm.get("audience_filter")

    if audience == "list" and isinstance(audience_filter, list):
        return len(audience_filter)

    session = container.session
    if audience == "all":
        row = await session.execute(
            text("SELECT COUNT(DISTINCT u.telegram_id) FROM users u JOIN career_week_registrations r ON r.user_id = u.id")
        )
    elif audience == "direction" and audience_filter:
        row = await session.execute(
            text("SELECT COUNT(DISTINCT u.telegram_id) FROM users u JOIN career_week_registrations r ON r.user_id = u.id WHERE r.direction = :f"),
            {"f": audience_filter},
        )
    elif audience == "course" and audience_filter:
        row = await session.execute(
            text("SELECT COUNT(DISTINCT u.telegram_id) FROM users u JOIN career_week_registrations r ON r.user_id = u.id WHERE r.course = :f"),
            {"f": audience_filter},
        )
    else:
        return 0
    return row.scalar() or 0


async def _get_recipient_ids(container: Container, fsm: dict) -> list[int]:
    audience = fsm.get("audience", "all")
    audience_filter = fsm.get("audience_filter")

    if audience == "list" and isinstance(audience_filter, list):
        return audience_filter

    session = container.session
    if audience == "all":
        rows = await session.execute(
            text("SELECT DISTINCT u.telegram_id FROM users u JOIN career_week_registrations r ON r.user_id = u.id")
        )
    elif audience == "direction" and audience_filter:
        rows = await session.execute(
            text("SELECT DISTINCT u.telegram_id FROM users u JOIN career_week_registrations r ON r.user_id = u.id WHERE r.direction = :f"),
            {"f": audience_filter},
        )
    elif audience == "course" and audience_filter:
        rows = await session.execute(
            text("SELECT DISTINCT u.telegram_id FROM users u JOIN career_week_registrations r ON r.user_id = u.id WHERE r.course = :f"),
            {"f": audience_filter},
        )
    else:
        return []
    return [r.telegram_id for r in rows.fetchall()]
