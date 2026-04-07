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


def _gdrive_direct_url(url: str) -> str:
    """Конвертирует Google Drive ссылку в прямую для скачивания."""
    if "drive.google.com" in url and "id=" in url:
        file_id = url.split("id=")[1].split("&")[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


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

    day = partner.get("day", "")
    time = partner.get("time", "")
    roast_direction = partner.get("roast_direction", "")

    lines = [f"🏢 <b>{partner['name']}</b>", "", partner.get("description", "")]
    if day and time:
        lines.append(f"\n📅 На неделе карьеры: {day}, {time}")
    elif day:
        lines.append(f"\n📅 На неделе карьеры: {day}")
    if roast_direction:
        lines.append(f"🔥 Прожарки: {roast_direction}")

    text = "\n".join(lines)
    keyboard = _partner_detail_keyboard(roast_direction) if roast_direction else _back_keyboard()

    logo_url = partner.get("logo_url", "")
    if logo_url:
        download_url = _gdrive_direct_url(logo_url)
        try:
            async with httpx.AsyncClient(
                verify=False,
                follow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            ) as client:
                resp = await client.get(download_url, timeout=10)
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
            logger.warning("Не удалось загрузить логотип %s", download_url)

    # Fallback — только текст
    await callback.message.answer(  # type: ignore[union-attr]
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )
