from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# ── Направления обучения ──────────────────────────────────────────────────────

DIRECTIONS = [
    ("💼 Бизнес и менеджмент",        "business"),
    ("📊 Финансы и банковское дело",   "finance"),
    ("📣 Маркетинг",                   "marketing"),
    ("💻 Бизнес-информатика",          "it"),
    ("🌍 Международный бизнес",        "international"),
    ("📋 Другое",                      "other"),
]
DIRECTION_LABELS: dict[str, str] = {key: label for label, key in DIRECTIONS}

# ── Курсы ─────────────────────────────────────────────────────────────────────

COURSES = ["1 курс", "2 курс", "3 курс", "4 курс", "Магистратура"]

# ── Навыки ────────────────────────────────────────────────────────────────────

SKILLS_LIST: list[str] = [
    # Технические
    "Excel", "Python", "SQL", "PowerPoint", "Финмодели",
    "Figma", "VBA", "R", "Tableau", "Power BI", "Bloomberg", "1С",
    # Языки
    "Английский B2+", "Английский C1+", "Немецкий",
    "Французский", "Китайский", "Испанский",
    # Soft
    "Управление проектами", "Публичные выступления", "Аналитическое мышление",
]


# ── Клавиатуры ────────────────────────────────────────────────────────────────

def directions_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=f"cw:dir:{key}")]
        for label, key in DIRECTIONS
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def level_keyboard() -> InlineKeyboardMarkup:
    """Выбор уровня образования — бакалавриат или магистратура."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎓 Бакалавриат", callback_data="cw:level:бакалавриат")],
            [InlineKeyboardButton(text="🎓 Магистратура", callback_data="cw:level:магистратура")],
        ]
    )


def programs_keyboard(programs: list[str]) -> InlineKeyboardMarkup:
    """Список образовательных программ + кнопка «Другое»."""
    rows = [
        [InlineKeyboardButton(text=prog, callback_data=f"cw:prog:{prog}")]
        for prog in programs
    ]
    rows.append([InlineKeyboardButton(text="✏️ Другое", callback_data="cw:prog:__other__")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def courses_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=course, callback_data=f"cw:course:{course}")]
        for course in COURSES
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def skills_keyboard(
    selected: list[str],
    skills_list: list[str] | None = None,
) -> InlineKeyboardMarkup:
    """
    Мультиселект навыков.
    skills_list — динамический список из кэша; если None — используется SKILLS_LIST.
    """
    source = skills_list if skills_list is not None else SKILLS_LIST
    rows: list[list[InlineKeyboardButton]] = []
    # По 2 навыка в ряд
    for i in range(0, len(source), 2):
        row = []
        for skill in source[i:i + 2]:
            prefix = "✓ " if skill in selected else ""
            row.append(InlineKeyboardButton(
                text=f"{prefix}{skill}",
                callback_data=f"cw:skill:{skill}",
            ))
        rows.append(row)
    # Кнопка "Другое"
    rows.append([InlineKeyboardButton(text="✏️ Другое", callback_data="cw:skill:__other__")])
    # Кнопка подтверждения
    rows.append([InlineKeyboardButton(text="✅ Готово", callback_data="cw:skills_done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def career_week_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Программа мероприятий", callback_data="cw:schedule")],
            [InlineKeyboardButton(text="🏢 Компании-партнёры",     callback_data="cw:partners")],
            [InlineKeyboardButton(text="🔥 Записаться на прожарку", callback_data="cw:roasts")],
            [InlineKeyboardButton(text="📝 Мои записи",            callback_data="cw:my_bookings")],
            [InlineKeyboardButton(text="← Главное меню Стажки",   callback_data="cw:exit")],
        ]
    )


# Алиас для использования из хендлеров
career_week_main_keyboard = career_week_menu_keyboard


def back_to_cw_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="← Главное меню недели", callback_data="cw:menu")]
        ]
    )
