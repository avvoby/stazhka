# API Reference — Стажка

## Обзор

FastAPI-приложение запускается на `API_HOST:API_PORT` (по умолчанию `0.0.0.0:8000`).
Swagger UI доступен по адресу `/docs`.

Сейчас реализованы только health-check эндпоинты. REST API для Mini App — в планах (v3).

---

## Эндпоинты

### GET /health

Быстрая проверка — возвращает статус без обращения к БД и Redis.

**Ответ:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

**Коды ответа:** `200 OK`

---

### GET /api/health

Расширенная проверка — тестирует подключение к PostgreSQL и Redis.

**Ответ (всё ок):**
```json
{
  "status": "ok",
  "db": "ok",
  "redis": "ok"
}
```

**Ответ (деградация):**
```json
{
  "status": "degraded",
  "db": "error",
  "redis": "ok"
}
```

**Коды ответа:** `200 OK` (даже при `degraded` — HTTP-статус всегда 200, деградация
определяется по полю `status` в теле ответа)

**Как работает:**
- PostgreSQL: `SELECT 1` через `AsyncSessionFactory`
- Redis: `PING` через `aioredis.from_url` с таймаутом 2 секунды

---

## Конфигурация FastAPI

```python
app = FastAPI(
    title="Стажка API",
    version="0.1.0",
    docs_url="/docs",
)
```

CORS настроен на `allow_origins=["*"]` — принимает запросы от любого origin.
Это сделано для разработки; перед продакшн-деплоем следует ограничить список origins.

---

## Авторизация

Авторизация в API **не реализована**. Все эндпоинты публичны.

Причина: сейчас API используется только для health-check мониторинга.
При добавлении Mini App потребуется авторизация через Telegram WebApp `initData`.

---

## Запуск API-сервера

API-сервер (`uvicorn`) запускается отдельно от Telegram-бота:

```bash
# Через Docker Compose
docker compose up -d api

# Или напрямую
uvicorn src.interface.api.app:app --host 0.0.0.0 --port 8000 --reload
```

В `docker-compose.yml` API описан как отдельный сервис с зависимостью от `db` и `redis`.

---

## Планы (v3): Mini App API

При добавлении Telegram Mini App планируются следующие эндпоинты:

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/auth/telegram` | Верификация `initData` от Telegram WebApp |
| `GET`  | `/api/me` | Профиль текущего пользователя |
| `GET`  | `/api/applications` | Список заявок пользователя |
| `POST` | `/api/applications` | Добавить заявку |
| `PATCH`| `/api/applications/{id}` | Обновить стадию |
| `GET`  | `/api/vacancies/search` | Поиск вакансий |

Авторизация: Telegram `initData` в заголовке `X-Telegram-Init-Data`, верификация
через HMAC-SHA256 с `BOT_TOKEN` как ключом.
