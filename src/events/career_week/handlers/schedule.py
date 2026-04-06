"""
Хендлеры: Программа мероприятий Весенней недели карьеры.
"""
import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from src.interface.telegram.middlewares.container import Container

logger = logging.getLogger(__name__)

router = Router(name="career_week_schedule")


def _days_keyboard(days: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"📅 {day}", callback_data=f"cw_day:{day}")]
        for day in days
    ]
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="cw:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _day_events_keyboard(day: str, events: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"{e.get('time_start', '')} — {e.get('title', '')} · {e.get('location', '')}",
            callback_data=f"cw_event:{day}:{idx}",
        )]
        for idx, e in enumerate(events)
    ]
    rows.append([InlineKeyboardButton(text="← К выбору дня", callback_data="cw:schedule")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _event_detail_keyboard(day: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="← К программе дня", callback_data=f"cw_day:{day}")],
            [InlineKeyboardButton(text="← К выбору дня", callback_data="cw:schedule")],
        ]
    )


@router.callback_query(F.data == "cw:schedule")
async def handle_schedule(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    cache = container.cw_cache
    schedule = await cache.get_schedule() if cache else []

    if not schedule:
        await callback.message.answer(  # type: ignore[union-attr]
            "📋 <b>Программа мероприятий</b>\n\nРасписание скоро появится!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="cw:menu")]]
            ),
            parse_mode="HTML",
        )
        return

    # Собираем уникальные дни (сохраняем порядок)
    seen: set[str] = set()
    days: list[str] = []
    for event in schedule:
        day = str(event.get("day", ""))
        if day and day not in seen:
            seen.add(day)
            days.append(day)

    await callback.message.answer(  # type: ignore[union-attr]
        "📋 <b>Программа мероприятий</b>\n\nВыбери день:",
        reply_markup=_days_keyboard(days),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("cw_day:"))
async def handle_day_schedule(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    day = (callback.data or "").split("cw_day:", 1)[1]

    cache = container.cw_cache
    schedule = await cache.get_schedule() if cache else []
    events = [e for e in schedule if str(e.get("day", "")) == day]

    if not events:
        await callback.message.answer(  # type: ignore[union-attr]
            f"На день «{day}» событий не найдено.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="← К выбору дня", callback_data="cw:schedule")]]
            ),
        )
        return

    await callback.message.answer(  # type: ignore[union-attr]
        f"📅 <b>{day}</b>\n\nВыбери событие:",
        reply_markup=_day_events_keyboard(day, events),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("cw_event:"))
async def handle_event_detail(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    _, day, idx_str = (callback.data or "").split(":", 2)

    cache = container.cw_cache
    schedule = await cache.get_schedule() if cache else []
    events = [e for e in schedule if str(e.get("day", "")) == day]

    try:
        event = events[int(idx_str)]
    except (IndexError, ValueError):
        await callback.message.answer("Событие не найдено.")  # type: ignore[union-attr]
        return

    text = (
        f"📌 <b>{event.get('title', '')}</b>\n"
        f"🕐 {event.get('time_start', '')} — {event.get('time_end', '')}\n"
        f"📍 {event.get('location', '')}\n\n"
        f"{event.get('description', '')}"
    )
    await callback.message.answer(  # type: ignore[union-attr]
        text,
        reply_markup=_event_detail_keyboard(day),
        parse_mode="HTML",
    )
