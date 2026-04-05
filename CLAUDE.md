# Стажка — Telegram-бот ассистент для стажировок

## Стек
Python 3.11, aiogram 3.13, FastAPI 0.115, PostgreSQL, SQLAlchemy 2.0,
Redis, OpenRouter (Claude API), APScheduler 3.x, Docker Compose

## Архитектура
Clean Architecture, 4 слоя:
- domain/ — чистые dataclasses, value objects, Protocol-интерфейсы
- application/ — use cases, services (aggregator, matching)
- infrastructure/ — SQLAlchemy, AI (OpenRouter), hh.ru / SuperJob / Telethon, Redis, Scheduler
- interface/ — Telegram handlers, keyboards, middlewares, FSM states

## Запуск
```bash
cd stazka
docker compose up -d db redis
docker compose --profile migrate up migrations
docker compose up -d --build bot
docker compose logs bot --tail=20
```

## Ключевые решения
- Repository Pattern через Protocol (не ABC)
- FSM только для многошаговых форм
- AI-парсинг контекста через asyncio.create_task (не блокирует)
- Rate limiting через Redis: rl:{user_id}:{action}:{date}
- ContainerMiddleware создаёт сессию на каждый апдейт
- Mock-сессии хранятся в Redis (ключ: mock:{user_id}:{session_id}, TTL 2ч)

## AI провайдер
OpenRouter (не прямой Anthropic API)
- Base URL: https://openrouter.ai/api/v1/chat/completions
- Fast model: `anthropic/claude-haiku-3-5-20251001`
- Quality model: `anthropic/claude-sonnet-4-5`
- verify=False (корпоративный SSL на ноутбуке разработчика)
- Клиент: httpx.AsyncClient с заголовком Authorization: Bearer {key}

---

## Текущий статус проекта

### v1 — Готово и работает
- Онбординг (3 шага: специализация, навыки, компании мечты)
- Трекер заявок (добавление вручную, по ссылке, с карточки поиска)
- Поиск на hh.ru с фильтром noExperience
- Cover letter через Claude API
- Профиль пользователя с редактированием
- /menu как якорь из любого состояния
- Feedback система (👎/⭐) с сохранением в vacancy_feedback
- Команда /start с онбордингом

### v2 Волна 1 — Готово
- VacancyAggregator: параллельный сбор из hh.ru + SuperJob + TG (заглушка)
- MatchingService: 3-уровневый матчинг (фильтр → keyword → Claude scoring)
- ScoredVacancy: скор 0–100 + explanation от Claude
- Новый формат карточки вакансии с AI-объяснением и 🎯 совпадением
- Кнопка "Показать ещё 5" (кэш в FSM state)
- Кнопка "⚙️ Изменить поиск" (быстрый FSM: специализация / навыки / город / сброс)
- Исключение дизлайкнутых вакансий при следующем поиске
- Таблица vacancy_feedback в БД (миграция 0002)

### v2 Волна 2 — Код написан, требует проверки
- Mock-интервью FSM (5 вопросов + разбор каждого ответа + итоговый отчёт)
  - Сессии в Redis (mock:{user_id}:{session_id})
  - БАГ в процессе отладки: проверяем slug quality_model
  - Текущие slugи: fast=`anthropic/claude-haiku-3-5-20251001`, quality=`anthropic/claude-sonnet-4-5`
- Личный кабинет v2: статистика заявок + воронка + расширенный профиль
  - Новые поля: gpa, language, experience, expected_salary, notifications_enabled
  - Миграция 0003
- APScheduler (3 задачи, timezone=Europe/Moscow):
  - 09:00 — напоминание перед интервью (next_step_date = завтра)
  - 10:00 — followup по заявкам в статусе applied > 7 дней
  - 10:00 — дайджест 3 вакансий под профиль

---

## Миграции БД
| # | Файл | Содержимое |
|---|---|---|
| 0001 | initial | users, user_profiles, vacancies, applications |
| 0002 | vacancy_feedback | таблица vacancy_feedback |
| 0003 | extend_user_profile | gpa, language, experience, expected_salary, notifications_enabled |

---

## Источники вакансий

**hh.ru** — активен (src/infrastructure/external/hh_client.py)
- per_page=50, experience=noExperience, area=1 (Москва)

**SuperJob** — написан, не активен (нет API ключа)
- src/infrastructure/external/superjob_client.py
- Получить ключ: https://api.superjob.ru

**Telegram-каналы** — заглушка (нет api_id/api_hash)
- src/infrastructure/external/telegram_parser.py
- Получить ключи: https://my.telegram.org
- Каналы (добавить в .env TELEGRAM_CHANNELS):
  pmclub, budujobs, studreru, vrabote_me, vacanciesbest,
  Axenix_Ru, tedo_career, gpbcareer, ozoncamp, magnit_students,
  RSHB_CAREER, b1_careers, chernogolovka_profuture, avito_career, pmiru_job

**Веб-сайты** (не реализованы, v3):
- axenix.tech/internship
- intern.t2.ru
- groundupcareer.ru

---

## Известные проблемы
1. Mock-интервью: отлаживаем slug quality_model на OpenRouter
2. Telegram parser: заглушка, возвращает [] (нет api_id/api_hash)
3. SuperJob: клиент написан, не активен (нет API ключа)

---

## Нереализовано (v3)
- Голосовые сообщения в Mock-интервью (Whisper API)
- Telegram-каналы парсинг (нужен api_id + api_hash)
- SuperJob интеграция (нужен API ключ)
- FastAPI routers для Mini App
- Деплой на VPS (бот работает только локально)
- GitHub репозиторий
- Монетизация / платный tier
- Полные unit тесты
