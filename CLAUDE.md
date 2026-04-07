# Стажка — Telegram-бот ассистент для стажировок

## Стек
Python 3.11, aiogram 3.x, FastAPI, PostgreSQL, SQLAlchemy 2.0,
Redis, Claude API через OpenRouter, Docker Compose,
gspread (Google Sheets API)

## Запуск локально
1. `cp .env.example .env` — заполнить все переменные
2. `docker compose up -d db redis`
3. `docker compose --profile migrate up migrations --build`
4. `docker compose up -d --build bot`
5. `docker compose logs bot --tail=20`

## Деплой на сервер
```bash
ssh -i ~/.ssh/ssh-key-1773246529615 avvoby@213.165.196.186
cd stazhka && git pull
docker compose up -d --build bot
```

## Переменные окружения (все обязательные)
```
TELEGRAM_BOT_TOKEN
DATABASE_URL
POSTGRES_USER, POSTGRES_DB, POSTGRES_PASSWORD
OPENROUTER_API_KEY
REDIS_URL
CAREER_WEEK_ENABLED        # true/false
CAREER_WEEK_ADMIN_IDS      # [5645685337]
GOOGLE_SHEETS_ID
GOOGLE_SERVICE_ACCOUNT_JSON
```

## Архитектура (4 слоя Clean Architecture)
```
domain/              — entities, value objects, repository protocols
application/         — use cases, services (AI, matching, aggregator)
infrastructure/      — SQLAlchemy, Claude/OpenRouter, hh.ru, SuperJob
interface/           — Telegram handlers, FastAPI, keyboards, FSM states
events/career_week/  — временный модуль (отключается флагом)
```

## Основной функционал (v1 + v2)
- Онбординг (3 шага: специализация, навыки, компании мечты)
- Поиск вакансий: агрегатор hh.ru + SuperJob + TG (заглушка)
- AI-матчинг 3 уровня: фильтр → keyword scoring → Claude scoring
- Трекер заявок: добавление вручную / по ссылке / с карточки
- Cover letter через Claude (OpenRouter)
- Mock-интервью: 5 вопросов + разбор + итоговый отчёт
- Личный кабинет: статистика, расширенный профиль, прогресс
- Напоминания через APScheduler
- Feedback система (👎/⭐) — дизлайкнутые не показываются снова
- /menu — возврат в главное меню из любого состояния

## Модуль Недели карьеры (v2.1)
Расположение: `src/events/career_week/`
Включение: `CAREER_WEEK_ENABLED=true` в `.env`
Отключение: `CAREER_WEEK_ENABLED=false` — кнопка исчезает,
            весь функционал недоступен, данные сохраняются

**Функционал:**
- Регистрация участника (5 шагов) + уникальный 5-значный код
- Компании-партнёры с логотипами (из Google Sheets)
- Программа мероприятий (3 уровня навигации)
- Запись на прожарки резюме/собеседований
- Загрузка резюме (файл PDF/фото или ссылка)
- Отмена записи, несколько записей разрешены
- Мои записи

**Админ-панель (/cwadmin):**
- Доступна только администраторам (telegram_id в листе admins)
- Суперадмин (всегда): 5645685337
- Рассылка: всем / по направлению / по курсу / по списку TG ID
- Обновить контент из Google Sheets
- Управление администраторами
- Статистика регистраций
- Резюме участников (скачивание файлов прямо в чат)

**Google Sheets** (ID: `1cKE-HP2Lj3fMYcBcTCdJ4_F-FX-FWp-AvUEIMZPLb4A`):
Листы: `partners`, `schedule`, `roast_slots`, `programs`, `skills`,
       `admins`, `registrations`, `roast_registrations`

## AI провайдер
OpenRouter: `https://openrouter.ai/api/v1/chat/completions`
- Fast model: `anthropic/claude-haiku-3-5-20251001`
- Quality model: `anthropic/claude-sonnet-4-5`
- `verify=False` (корпоративный SSL на ноутбуке разработчика)

## Миграции БД
| # | Содержимое |
|---|---|
| 0001 | initial (users, user_profiles, vacancies, applications) |
| 0002 | vacancy_feedback |
| 0003 | extend_user_profile (gpa, language, experience, expected_salary, notifications_enabled) |
| 0004 | career_week_tables (career_week_registrations, career_week_roast_bookings, career_week_slots_cache) |

## TG-каналы для парсинга (когда получим ключи)
```
pmclub, budujobs, studreru, vrabote_me, vacanciesbest,
Axenix_Ru, tedo_career, gpbcareer, ozoncamp, magnit_students,
RSHB_CAREER, b1_careers, chernogolovka_profuture,
avito_career, pmiru_job
```
Получить ключи: https://my.telegram.org → `TELEGRAM_CHANNELS` в `.env`

## Известные проблемы / TODO
- TG-парсер: заглушка, нужен `api_id` + `api_hash` (my.telegram.org)
- SuperJob: клиент написан, нужен API ключ (api.superjob.ru)
- FastAPI роутеры для Mini App: не реализованы (v3)
- Деплой: бот на Yandex Cloud VM `213.165.196.186`

## GitHub
https://github.com/avvoby/stazhka
