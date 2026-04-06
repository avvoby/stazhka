"""
Хендлеры: Компании-партнёры Весенней недели карьеры.
"""
import logging

import httpx
from aiogram import F, Router
from aiogram.types import BufferedInputFile, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from src.domain.entities.user import User
from src.interface.telegram.middlewares.container import Container

logger = logging.getLogger(__name__)

router = Router(name="career_week_partners")


def _partners_list_keyboard(partners: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text=f"🏢 {p['name']}",
            callback_data=f"cw_partner:{p['name']}",
        )]
        for p in partners
    ]
    rows.append([InlineKeyboardButton(text="← Назад", callback_data="cw:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _partner_detail_keyboard(roast_direction: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🔥 Записаться на прожарку {roast_direction}",
                callback_data=f"cw:roasts:dir:{roast_direction}",
            )],
            [InlineKeyboardButton(text="← К списку партнёров", callback_data="cw:partners")],
        ]
    )


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="← Назад", callback_data="cw:menu")]]
    )


@router.callback_query(F.data == "cw:partners")
async def handle_partners_list(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    cache = container.cw_cache
    partners = await cache.get_partners() if cache else []

    if not partners:
        await callback.message.answer(  # type: ignore[union-attr]
            "🏢 <b>Компании-партнёры</b>\n\nСписок партнёров скоро появится!",
            reply_markup=_back_keyboard(),
            parse_mode="HTML",
        )
        return

    await callback.message.answer(  # type: ignore[union-attr]
        "🏢 <b>Компании-партнёры</b>\n\nВыбери компанию, чтобы узнать подробнее:",
        reply_markup=_partners_list_keyboard(partners),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("cw_partner:"))
async def handle_partner_detail(
    callback: CallbackQuery,
    container: Container,
) -> None:
    await callback.answer()
    name = (callback.data or "").split("cw_partner:", 1)[1]

    cache = container.cw_cache
    partners = await cache.get_partners() if cache else []
    partner = next((p for p in partners if p.get("name") == name), None)

    if not partner:
        await callback.message.answer(  # type: ignore[union-attr]
            "Партнёр не найден.",
            reply_markup=_back_keyboard(),
        )
        return

    text = (
        f"🏢 <b>{partner['name']}</b>\n\n"
        f"{partner.get('description', '')}\n\n"
        f"📅 На неделе карьеры: {partner.get('day', '—')}, {partner.get('time', '—')}\n"
        f"🔥 Прожарки: {partner.get('roast_direction', '—')}"
    )
    keyboard = _partner_detail_keyboard(partner.get("roast_direction", ""))

    logo_url = partner.get("logo_url", "")
    if logo_url:
        try:
            async with httpx.AsyncClient(timeout=10, verify=False) as client:
                resp = await client.get(logo_url)
                resp.raise_for_status()
                photo = BufferedInputFile(resp.content, filename="logo.jpg")
            await callback.message.answer_photo(  # type: ignore[union-attr]
                photo=photo,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            return
        except Exception:
            logger.warning("Не удалось загрузить логотип %s", logo_url)

    # Fallback — только текст
    await callback.message.answer(  # type: ignore[union-attr]
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
