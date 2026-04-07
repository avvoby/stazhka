# Архитектура Стажки

## Обзор

Стажка построена по принципам Clean Architecture с четырьмя слоями.
Зависимости направлены строго внутрь: infrastructure → application → domain.
Модуль `events/career_week/` — временный, отключается флагом окружения.

---

## Слои

```
┌───────────────────────────────────────────────────────────────┐
│  interface/                                                    │
│  Telegram handlers, keyboards, FSM states, FastAPI routers     │
├───────────────────────────────────────────────────────────────┤
│  application/                                                  │
│  use_cases, VacancyAggregator, MatchingService, AIService      │
├───────────────────────────────────────────────────────────────┤
│  infrastructure/                                               │
│  SQLAlchemy repos, OpenRouter client, hh.ru, SuperJob, Redis   │
├───────────────────────────────────────────────────────────────┤
│  domain/                                                       │
│  User, Vacancy, Application entities + repository Protocols    │
└───────────────────────────────────────────────────────────────┘
         ↑ зависимость только вниз
┌───────────────────────────────────────────────────────────────┐
│  events/career_week/                                           │
│  Временный модуль недели карьеры (отключается флагом)          │
└───────────────────────────────────────────────────────────────┘
```

---

## Структура директорий

```
src/
├── core/
│   └── config.py               — pydantic-settings, синглтон settings
├── domain/
│   ├── entities/               — User, Vacancy, Application (dataclasses)
│   ├── value_objects/          — SearchStatus, ApplicationStage, VacancySource
│   └── repositories/           — Protocol-интерфейсы репозиториев
├── application/
│   ├── use_cases/              — onboarding, vacancies, applications, ai_features
│   └── services/               — VacancyAggregator, MatchingService
├── infrastructure/
│   ├── database/
│   │   ├── models.py           — SQLAlchemy ORM модели
│   │   ├── connection.py       — AsyncSessionFactory
│   │   └── repositories/       — реализации Protocol-репозиториев
│   ├── ai/
│   │   ├── claude_service.py   — OpenRouter / Claude клиент
│   │   └── rate_limiter.py     — Redis rate limiting
│   └── external/
│       ├── hh_client.py        — hh.ru API (активен)
│       ├── superjob_client.py  — SuperJob API (написан, нет ключа)
│       └── telegram_parser.py  — TG-каналы (заглушка, нет api_id)
├── interface/
│   ├── telegram/
│   │   ├── handlers/           — onboarding, vacancies, applications, profile
│   │   ├── keyboards/          — inline и reply клавиатуры
│   │   ├── middlewares/        — ContainerMiddleware, AuthMiddleware
│   │   └── states/             — FSM StatesGroups
│   └── api/
│       ├── app.py              — FastAPI app
│       └── routers/health.py   — /health endpoint
├── events/
│   └── career_week/
│       ├── config.py           — CareerWeekSettings (env_prefix=CAREER_WEEK_)
│       ├── models.py           — CareerWeekRegistration, RoastBooking, RoastSlot
│       ├── handlers/
│       │   ├── main.py         — регистрация (5 шагов), главное меню
│       │   ├── partners.py     — компании-партнёры с логотипами
│       │   ├── schedule.py     — программа мероприятий
│       │   ├── roasts.py       — запись на прожарки, отмена, мои записи
│       │   └── admin.py        — /cwadmin: рассылка, контент, статистика
│       ├── keyboards/
│       │   └── main.py         — все клавиатуры модуля
│       └── services/
│           ├── sheets.py       — Google Sheets (gspread, asyncio.to_thread)
│           ├── cache.py        — Redis кэш (TTL 24ч), sync_from_sheets()
│           └── registration.py — регистрация, генерация кода, атомарное бронирование
└── main.py                     — точка входа, build_dispatcher(), APScheduler
```

---

## Поток данных: поиск вакансий

```
Telegram update
    → ContainerMiddleware (создаёт session, ai_service, hh_client)
    → AuthMiddleware (проверяет user + profile)
    → VacanciesHandler
        → VacancyAggregator.search()
            ├── hh_client.search()       — реальный запрос
            ├── superjob_client.search() — заглушка (нет ключа)
            └── telegram_parser.parse()  — заглушка (нет api_id)
        → MatchingService.score()
            ├── уровень 1: фильтр по специализации/навыкам
            ├── уровень 2: keyword scoring (TF-IDF-подобный)
            └── уровень 3: Claude scoring (0-100 + explanation)
        → FSM state (кэш результатов, "Показать ещё 5")
```

---

## Поток данных: модуль Недели карьеры

```
CAREER_WEEK_ENABLED=true
    → main.py: загружает CW-сервисы, регистрирует роутеры
    → sync_from_sheets() при старте
        → GoogleSheetsService (gspread) читает 6 листов
        → CareerWeekCacheService пишет в Redis (TTL 24ч)
        → career_week_slots_cache в PostgreSQL (capacity)

Telegram update → CW handlers
    → container.cw_cache (Redis) — данные о партнёрах, слотах, программах
    → container.cw_registration — запись, бронирование, генерация кода
    → Google Sheets запись (asyncio.create_task — не блокирует)
```

---

## Атомарное бронирование слота

```sql
UPDATE career_week_slots_cache
SET registrations_count = registrations_count + 1,
    updated_at = now()
WHERE slot_id = :slot_id
  AND registrations_count < capacity
RETURNING registrations_count
```
Если `RETURNING` возвращает 0 строк — слот заполнен, пользователь получает уведомление.

---

## APScheduler задачи (timezone=Europe/Moscow)

| Время | Задача |
|-------|--------|
| 09:00 | Напоминание перед интервью (next_step_date = завтра) |
| 10:00 | Follow-up по заявкам в статусе applied > 7 дней |
| 10:00 | Дайджест 3 вакансий под профиль пользователя |

---

## Таблицы БД

### Основные (миграции 0001–0003)

| Таблица | Содержимое |
|---------|-----------|
| `users` | telegram_id, username, display_name |
| `user_profiles` | специализация, навыки, компании мечты, gpa, language, expected_salary |
| `vacancies` | кэш вакансий из агрегатора |
| `applications` | трекер заявок пользователя |
| `vacancy_feedback` | лайки/дизлайки вакансий |

### Неделя карьеры (миграция 0004)

| Таблица | Содержимое |
|---------|-----------|
| `career_week_registrations` | user_id, code (5 символов), direction, program, course, skills |
| `career_week_roast_bookings` | user_id, slot_id, slot_type, direction, resume_file_id, resume_url, cancelled_at |
| `career_week_slots_cache` | slot_id, capacity, registrations_count (для атомарного бронирования) |

---

## Google Sheets интеграция

```
GoogleSheetsService
├── gspread 6.x + google-auth
├── Все методы async через asyncio.to_thread()
├── Timeout: 30 секунд на каждый запрос
├── Чтение: get_partners, get_schedule, get_roast_slots,
│           get_programs, get_skills, get_admins
└── Запись: append_registration, append_roast_booking,
            update_roast_cancellation, update_admins
```

Данные кэшируются в Redis (TTL 24ч). Обновление — через `/cwadmin → Обновить контент`.

---

## Схема деплоя

```
Yandex Cloud VM (213.165.196.186)
└── Docker Compose
    ├── bot        — aiogram polling, APScheduler, FastAPI
    ├── db         — PostgreSQL 16
    ├── redis      — Redis 7
    └── migrations — Alembic (profile=migrate, запускается вручную)
```

Все контейнеры: `restart: unless-stopped`.
Бот автоматически поднимается после перезагрузки сервера.

---

## Ключевые архитектурные решения

1. **Repository Pattern через Protocol** — не ABC, позволяет легко мокировать в тестах без наследования
2. **FSM только для многошаговых форм** — onboarding, registration, roast booking, broadcast
3. **AI-парсинг через asyncio.create_task** — не блокирует ответ пользователю
4. **Rate limiting через Redis** — ключ `rl:{user_id}:{action}:{date}`, INCR + EXPIRE в pipeline
5. **ContainerMiddleware** — создаёт DB-сессию на каждый update, ai_service/hh_client — синглтоны
6. **Career Week через TYPE_CHECKING** — CW-сервисы импортируются только если `CAREER_WEEK_ENABLED=true`, строковые аннотации в `build_dispatcher()` для runtime-безопасности
7. **Атомарное бронирование** — UPDATE ... WHERE count < capacity RETURNING, без race conditions
