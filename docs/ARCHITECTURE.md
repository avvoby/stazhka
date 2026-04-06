# Архитектура Стажки

## Обзор

Стажка построена по принципам Clean Architecture с четырьмя слоями.
Зависимости направлены строго внутрь: infrastructure → application → domain.

---

## Слои

```
┌─────────────────────────────────────────────────────┐
│  interface/                                          │
│  Telegram handlers, keyboards, FSM, FastAPI routers  │
├─────────────────────────────────────────────────────┤
│  application/                                        │
│  use_cases, services (aggregator, matching, AI)      │
├─────────────────────────────────────────────────────┤
│  infrastructure/                                     │
│  SQLAlchemy repos, hh.ru, SuperJob, Telethon, Redis  │
├─────────────────────────────────────────────────────┤
│  domain/                                             │
│  entities (User, Vacancy, Application)               │
│  value_objects, repository Protocols                 │
└─────────────────────────────────────────────────────┘
```

---

## Структура папок

```
src/
├── core/
│   ├── config.py            # Pydantic-settings, синглтон settings
│   └── container.py         # (резерв)
│
├── domain/
│   ├── entities/
│   │   ├── user.py          # User, UserProfile dataclasses
│   │   ├── vacancy.py       # Vacancy dataclass + свойства salary_display
│   │   └── application.py   # Application dataclass
│   ├── value_objects/
│   │   ├── application_stage.py  # Enum: saved/applied/screening/test/interview/offer/rejected
│   │   ├── vacancy_source.py     # Enum: hh_ru/superjob/telegram/manual
│   │   ├── search_status.py      # Enum: active/paused
│   │   └── work_format.py        # Enum: office/remote/hybrid/unspecified
│   └── repositories/
│       ├── user_repo.py          # Protocol UserRepository
│       ├── vacancy_repo.py       # Protocol VacancyRepository
│       └── application_repo.py   # Protocol ApplicationRepository
│
├── application/
│   ├── use_cases/
│   │   ├── onboarding.py         # GetOrCreateUser
│   │   ├── vacancies.py          # SearchVacancies, GetVacancy
│   │   ├── applications.py       # GetUserApplications, UpdateApplicationStage
│   │   └── ai_features.py        # MockInterviewUseCase (Redis сессии)
│   └── services/
│       ├── vacancy_aggregator.py # Параллельный сбор из 3 источников
│       └── matching_service.py   # 3-уровневый матчинг + Claude scoring
│
├── infrastructure/
│   ├── database/
│   │   ├── connection.py         # AsyncEngine + AsyncSessionFactory
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   └── repositories/
│   │       ├── user_repo.py
│   │       ├── vacancy_repo.py
│   │       ├── application_repo.py
│   │       └── feedback_repo.py
│   ├── ai/
│   │   ├── claude_service.py     # OpenRouter HTTP клиент
│   │   ├── mock_session.py       # Redis-хранилище сессий mock-интервью
│   │   └── rate_limiter.py       # Redis rate limiting
│   ├── external/
│   │   ├── hh_client.py          # hh.ru API (активен)
│   │   ├── superjob_client.py    # SuperJob API (выключен — нет ключа)
│   │   └── telegram_parser.py    # Telethon MTProto (заглушка — нет api_id)
│   └── scheduler/
│       └── tasks.py              # APScheduler cron-задачи
│
├── interface/
│   ├── telegram/
│   │   ├── handlers/
│   │   │   ├── onboarding.py     # /start, профиль, личный кабинет
│   │   │   ├── vacancies.py      # поиск, карточки, feedback
│   │   │   ├── applications.py   # трекер заявок
│   │   │   └── ai_features.py    # mock-интервью
│   │   ├── keyboards/
│   │   │   └── main.py           # все клавиатуры бота
│   │   ├── middlewares/
│   │   │   ├── container.py      # DI middleware (Container dataclass)
│   │   │   └── auth.py           # проверка завершённости онбординга
│   │   └── states/
│   │       └── forms.py          # все FSM StatesGroup
│   └── api/
│       ├── app.py                # FastAPI приложение
│       └── routers/
│           └── health.py         # /api/health
│
├── events/
│   └── career_week/              # изолированный модуль (см. ниже)
│
└── main.py                       # точка входа: bot + scheduler
```

---

## Поток данных (поиск вакансий)

```
Пользователь
    │ "🔍 Найти стажировку"
    ▼
Handler (vacancies.py)
    │ читает UserProfile из Container.user_repo
    ▼
VacancyAggregator.fetch_all(profile)
    │ asyncio.gather(hh_task, sj_task, tg_task)
    ├── HHClient.search_vacancies()  →  hh.ru API (2 страницы параллельно)
    ├── SuperJobClient.search_vacancies()  →  superjob.ru API (если ключ есть)
    └── TelegramChannelParser.fetch_vacancies()  →  Telethon (если api_id есть)
    │
    │ list[dict] — унифицированный формат
    ▼
MatchingService.match(vacancies, profile)
    │
    ├── L1: _hard_filter — убирает вакансии без слов специализации
    ├── L2: _keyword_score — score 30–100 по навыкам/должности/городу
    └── L3: _claude_score_batch — top-40 → Claude (OpenRouter) параллельно
    │
    │ list[ScoredVacancy] sorted by final_score
    ▼
Handler
    │ берёт первые PAGE_SIZE=5 из FSM-кэша
    │ сохраняет остаток в state для "Показать ещё 5"
    ▼
Пользователь видит карточки с 🎯 скором и AI-объяснением
```

---

## Описание слоёв

### domain/
Чистые Python-объекты без зависимостей на фреймворки.
- `entities/` — dataclasses с бизнес-логикой (свойства, методы)
- `value_objects/` — Enum-перечисления для типизации
- `repositories/` — Protocol-интерфейсы, описывают контракт без реализации

### application/
Бизнес-логика, не знает о Telegram и базе данных.
- `use_cases/` — сценарии использования, оперируют domain-объектами
- `services/` — сложная логика из нескольких источников (Aggregator, Matching)

### infrastructure/
Реализации технических деталей: SQL, HTTP, Redis.
- Репозитории реализуют Protocol из domain
- Клиенты инкапсулируют работу с внешними API
- Scheduler запускает cron-задачи независимо от Telegram

### interface/
Адаптеры для внешнего мира.
- Telegram handlers вызывают application use_cases
- FastAPI routers — только health check (Mini App в планах)
- FSM states описаны централизованно в `states/forms.py`

---

## Ключевые архитектурные решения

### Protocol вместо ABC
```python
# domain/repositories/vacancy_repo.py
class VacancyRepository(Protocol):
    async def get_by_id(self, id: UUID) -> Vacancy | None: ...
    async def search(self, query: str, ...) -> list[Vacancy]: ...
```
**Почему:** ABC создаёт наследование и жёсткую связанность. Protocol позволяет
реализовывать интерфейс без явного наследования — достаточно иметь нужные методы.
Тесты могут использовать любой объект с совместимой сигнатурой без моков ABC.

### DI через dataclass Container
```python
@dataclass
class Container:
    session: AsyncSession
    user_repo: UserRepositoryImpl
    ai_service: ClaudeAIService
    hh_client: HHClient
    ...
```
**Почему:** Явный граф зависимостей виден в одном месте. Нет магии IoC-контейнеров.
`ContainerMiddleware` создаёт Container на каждый Telegram-апдейт, что обеспечивает
изоляцию сессий и thread-safety. Синглтоны (ai_service, hh_client) создаются один раз
в `__init__` middleware.

### Сессия на каждый апдейт
```python
async with AsyncSessionFactory() as session:
    container = Container(session=session, ...)
    result = await handler(event, data)
    await session.commit()
```
**Почему:** Гарантирует атомарность каждого апдейта — или всё сохранилось, или ничего.
Не нужно думать об управлении транзакциями в хендлерах.

### FSM только для многошаговых форм
FSM (aiogram) используется только там, где пользователь проходит несколько шагов:
онбординг, добавление заявки, mock-интервью, запись на прожарку, рассылка.
Простые действия (лайк/дизлайк, смена статуса) — callback без FSM.

### AI через asyncio.create_task
```python
# Не блокирует — оценка идёт параллельно с другими вакансиями
tasks = [asyncio.create_task(self._claude_score_one(item, profile)) for item in items]
await asyncio.gather(*tasks, return_exceptions=True)
```
**Почему:** Claude scoring всех 40 вакансий последовательно занял бы 40+ секунд.
Параллельные задачи выполняются за время самой медленной (обычно 3–5 секунд).

### Rate limiting через Redis
```
rl:{user_id}:{action}:{date}  →  counter  (TTL до 23:59:59)
```
INCR + EXPIRE в одном pipeline(transaction=True).

### OpenRouter вместо прямого Anthropic API
Все AI-запросы идут через OpenRouter с заголовком `Authorization: Bearer {key}`.
`verify=False` — обход корпоративного SSL-инспектора на ноутбуке разработчика.
Модели: `anthropic/claude-haiku-3-5-20251001` (fast), `anthropic/claude-sonnet-4-5` (quality).

---

## Модуль Career Week (events/career_week/)

Временный изолированный модуль для Весенней недели карьеры ВШБ.

### Структура
```
src/events/career_week/
├── config.py           # CareerWeekSettings (CAREER_WEEK_ENABLED и др.)
├── models.py           # CareerWeekRegistration, RoastSlot, RoastBooking dataclasses
├── handlers/
│   ├── main.py         # регистрация участника (4-шаговый FSM), главное меню
│   ├── partners.py     # карточки компаний-партнёров с логотипами
│   ├── schedule.py     # программа мероприятий (3-уровневая навигация)
│   ├── roasts.py       # запись на прожарки, мои записи, отмена
│   └── admin.py        # /cwadmin: рассылка, обновление контента, статистика
├── keyboards/
│   └── main.py         # клавиатуры модуля
└── services/
    ├── registration.py # CareerWeekRegistrationService (raw SQL)
    ├── sheets.py       # GoogleSheetsService (asyncio.to_thread)
    └── cache.py        # CareerWeekCacheService (Redis TTL 24ч)
```

### Включение/выключение
```bash
# .env
CAREER_WEEK_ENABLED=true   # включить
CAREER_WEEK_ENABLED=false  # выключить
```
При `false` — кнопка не появляется в главном меню, роутеры не регистрируются.
Данные сохраняются в БД и Google Sheets после выключения.

### Изоляция
Модуль не импортируется напрямую основным кодом. В `main.py`:
```python
if career_week_settings.career_week_enabled:
    from src.events.career_week.handlers import main as cw_main
    dp.include_router(cw_main.router)
    ...
```
Container получает опциональные поля `cw_sheets`, `cw_cache`, `cw_registration`.

---

## Миграции БД

| # | Файл | Содержимое |
|---|------|------------|
| 0001 | 20260322_0000_0001_initial | users, user_profiles, vacancies, applications |
| 0002 | 20260404_0000_0002_vacancy_feedback | vacancy_feedback |
| 0003 | 20260404_0001_0003_extend_user_profile | gpa, language, experience, expected_salary, notifications_enabled |
| 0004 | 20260404_0002_0004_career_week | career_week_registrations, career_week_roast_bookings, career_week_slots_cache |

Запуск миграций:
```bash
docker compose --profile migrate up migrations
```

---

## Scheduler (APScheduler 3.x)

Три cron-задачи, timezone=Europe/Moscow:

| Время | Задача | Действие |
|-------|--------|----------|
| 09:00 | `check_interview_reminders` | Напоминание если `next_step_date` = завтра и стадия interview |
| 10:00 | `check_application_followups` | Followup если стадия applied > 7 дней без изменений |
| 10:00 | `send_daily_digest` | Дайджест 3 вакансий пользователям с `notifications_enabled=True` |
