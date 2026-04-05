from uuid import UUID

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.domain.value_objects.application_stage import ApplicationStage

# ── Справочники ──────────────────────────────────────────────────────────────

SPECIALIZATIONS = [
    ("💼 Финансы", "finance"),
    ("📊 Консалтинг", "consulting"),
    ("📣 Маркетинг", "marketing"),
    ("👥 HR", "hr"),
    ("⚙️ Операции", "operations"),
    ("💻 IT", "it"),
]

SPEC_LABELS: dict[str, str] = {key: label for label, key in SPECIALIZATIONS}

COURSES = [
    ("1 курс", "1"),
    ("2 курс", "2"),
    ("3 курс", "3"),
    ("4 курс", "4"),
    ("Магистратура", "master"),
]

COURSE_LABELS: dict[str, str] = {key: label for label, key in COURSES}

SKILLS_OPTIONS = [
    ("Excel", "excel"),
    ("Python", "python"),
    ("SQL", "sql"),
    ("PowerPoint", "powerpoint"),
    ("Английский B2+", "english_b2"),
    ("Финмодели", "finmodels"),
    ("Figma", "figma"),
    ("Другое", "other"),
]

SKILL_LABELS: dict[str, str] = {key: label for label, key in SKILLS_OPTIONS}


# ── Онбординг ────────────────────────────────────────────────────────────────

def privacy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Принимаю ✓", callback_data="privacy:accept")]
        ]
    )


def specialization_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text=label, callback_data=f"spec:{key}")
            for label, key in SPECIALIZATIONS[i:i + 2]
        ]
        for i in range(0, len(SPECIALIZATIONS), 2)
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def course_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"course:{key}")
             for label, key in COURSES[:2]],
            [InlineKeyboardButton(text=label, callback_data=f"course:{key}")
             for label, key in COURSES[2:4]],
            [InlineKeyboardButton(text=COURSES[4][0], callback_data=f"course:{COURSES[4][1]}")],
        ]
    )


def skills_keyboard(selected: list[str]) -> InlineKeyboardMarkup:
    rows = []
    row: list[InlineKeyboardButton] = []
    for label, key in SKILLS_OPTIONS:
        prefix = "✅ " if key in selected else ""
        row.append(InlineKeyboardButton(
            text=f"{prefix}{label}",
            callback_data=f"skill:{key}",
        ))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text="✅ Готово", callback_data="skills:done")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Профиль ──────────────────────────────────────────────────────────────────

def profile_edit_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Изменить специализацию", callback_data="edit:specialization")],
            [InlineKeyboardButton(text="Изменить курс", callback_data="edit:course")],
            [InlineKeyboardButton(text="Изменить навыки", callback_data="edit:skills")],
            [InlineKeyboardButton(text="Изменить компании", callback_data="edit:companies")],
        ]
    )


def profile_v2_keyboard(notifications_on: bool = True) -> InlineKeyboardMarkup:
    notif_text = "🔔 Уведомления вкл" if notifications_on else "🔕 Уведомления выкл"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=notif_text, callback_data="profile:toggle_notif")],
            [InlineKeyboardButton(text="🏢 Компании мечты", callback_data="edit:companies")],
            [InlineKeyboardButton(text="⚙️ Изменить профиль", callback_data="profile:edit_menu")],
            [InlineKeyboardButton(text="📈 Мой прогресс", callback_data="profile:progress")],
        ]
    )


def profile_edit_v2_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎓 Специализация", callback_data="edit:specialization"),
                InlineKeyboardButton(text="💡 Навыки", callback_data="edit:skills"),
            ],
            [
                InlineKeyboardButton(text="🏢 Компании", callback_data="edit:companies"),
                InlineKeyboardButton(text="📚 Курс", callback_data="edit:course"),
            ],
            [
                InlineKeyboardButton(text="📊 GPA", callback_data="edit:gpa"),
                InlineKeyboardButton(text="🌍 Язык", callback_data="edit:language"),
            ],
            [
                InlineKeyboardButton(text="💼 Опыт", callback_data="edit:experience"),
                InlineKeyboardButton(text="💰 Зарплата", callback_data="edit:salary"),
            ],
            [InlineKeyboardButton(text="← Назад", callback_data="profile:back")],
        ]
    )


# ── Главное меню ─────────────────────────────────────────────────────────────

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔍 Найти стажировку"),
                KeyboardButton(text="📋 Мои заявки"),
            ],
            [
                KeyboardButton(text="➕ Добавить вакансию"),
                KeyboardButton(text="👤 Профиль"),
            ],
        ],
        resize_keyboard=True,
        persistent=True,
    )


def add_vacancy_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Вручную", callback_data="add_vacancy:manual")],
            [InlineKeyboardButton(text="🔗 Вставить ссылку", callback_data="add_vacancy:url")],
            [InlineKeyboardButton(text="🔎 Найти на hh.ru", callback_data="add_vacancy:hh")],
        ]
    )


def application_stages_keyboard(application_id: UUID) -> InlineKeyboardMarkup:
    app_id = str(application_id)
    buttons: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="✍️ Написать письмо", callback_data=f"cover:{app_id}"),
            InlineKeyboardButton(text="🎤 Mock-интервью", callback_data=f"mock:app:{app_id}"),
        ],
    ]
    buttons += [
        [InlineKeyboardButton(
            text=stage.label,
            callback_data=f"stage:{app_id}:{stage.value}",
        )]
        for stage in ApplicationStage
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def mock_select_keyboard(applications: list) -> InlineKeyboardMarkup:
    """Список заявок для выбора вакансии mock-интервью."""
    rows = [
        [InlineKeyboardButton(
            text=f"🏢 {a.vacancy_title or 'Без названия'} — {a.vacancy_company or ''}",
            callback_data=f"mock:app:{a.id}",
        )]
        for a in applications
    ]
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="mock:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mock_finish_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Ещё раз", callback_data="mock:restart"),
                InlineKeyboardButton(text="📋 Мои заявки", callback_data="mock:to_apps"),
            ],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="mock:to_menu")],
        ]
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


# ── Вакансии ─────────────────────────────────────────────────────────────────

def vacancy_card_keyboard(
    vacancy_id: str,
    hh_url: str | None = None,
    show_feedback: bool = False,
) -> InlineKeyboardMarkup:
    top_row: list[InlineKeyboardButton] = []
    if hh_url:
        top_row.append(InlineKeyboardButton(text="🔗 Открыть", url=hh_url))
    top_row.append(InlineKeyboardButton(text="➕ Откликнуться", callback_data=f"apply:{vacancy_id}"))

    rows: list[list[InlineKeyboardButton]] = [top_row]
    if show_feedback:
        rows.append([
            InlineKeyboardButton(text="👎 Не моё", callback_data=f"fb:dislike:{vacancy_id}"),
            InlineKeyboardButton(text="⭐ Сохранить", callback_data=f"fb:like:{vacancy_id}"),
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vacancies_more_keyboard(offset: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Показать ещё 5", callback_data=f"vacancies:more:{offset}")]
        ]
    )


# ── Заявки ───────────────────────────────────────────────────────────────────

def applications_add_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить вручную", callback_data="app:add_manual")]
        ]
    )


def stage_selection_keyboard() -> InlineKeyboardMarkup:
    stages = [
        ("💾 Сохранена", "saved"),
        ("📤 Подана", "applied"),
        ("📞 Скрининг", "screening"),
        ("📝 Тест", "test"),
        ("🎤 Интервью", "interview"),
    ]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t, callback_data=f"new_stage:{v}") for t, v in stages[:2]],
            [InlineKeyboardButton(text=t, callback_data=f"new_stage:{v}") for t, v in stages[2:4]],
            [InlineKeyboardButton(text=stages[4][0], callback_data=f"new_stage:{stages[4][1]}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="app:cancel")],
        ]
    )


def search_settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎓 Специализация", callback_data="search:spec"),
                InlineKeyboardButton(text="💡 Навыки", callback_data="search:skills"),
            ],
            [
                InlineKeyboardButton(text="📍 Город", callback_data="search:city"),
                InlineKeyboardButton(text="🔄 Сбросить фильтры", callback_data="search:reset"),
            ],
        ]
    )


def search_change_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⚙️ Изменить поиск", callback_data="search:settings")]
        ]
    )


def followup_keyboard(application_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, позвали", callback_data=f"followup:yes:{application_id}"),
                InlineKeyboardButton(text="❌ Отказали", callback_data=f"followup:no:{application_id}"),
            ],
            [InlineKeyboardButton(text="⏳ Жду", callback_data=f"followup:wait:{application_id}")],
        ]
    )


def interview_reminder_keyboard(application_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎤 Mock-интервью", callback_data=f"mock:app:{application_id}")],
            [InlineKeyboardButton(text="✅ Готов", callback_data=f"interview:ready:{application_id}")],
        ]
    )


def digest_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Смотреть подборку", callback_data="digest:search")]
        ]
    )


def skip_url_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Пропустить", callback_data="app:skip_url")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="app:cancel")],
        ]
    )
