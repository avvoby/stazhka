# Источники вакансий — Стажка

## Как устроен VacancyAggregator

`src/application/services/vacancy_aggregator.py`

Агрегатор запускает три источника **параллельно** через `asyncio.gather`.
Ошибка в одном источнике не ломает остальные — каждый оборачивается в `try/except`,
при ошибке возвращает `[]` и пишет в лог.

```python
hh_task  = asyncio.create_task(self._fetch_hh(hh_query, filters))
sj_task  = asyncio.create_task(self._fetch_sj(sj_query))
tg_task  = asyncio.create_task(self._fetch_tg())

hh_results, sj_results, tg_results = await asyncio.gather(
    hh_task, sj_task, tg_task, return_exceptions=False
)
```

Все источники возвращают данные в **унифицированном формате** (dict).
После сбора список передаётся в `MatchingService` для 3-уровневого матчинга.

---

## Унифицированный формат (RawVacancy dict)

Все источники возвращают список dict с одинаковыми ключами:

| Поле | Тип | Описание |
|------|-----|----------|
| `source` | `str` | `"hh"` / `"superjob"` / `"telegram"` |
| `source_id` | `str` | Уникальный ID в рамках источника |
| `title` | `str` | Название вакансии |
| `company` | `str` | Название компании |
| `city` | `str` | Город (может быть пустым) |
| `description` | `str` | Описание вакансии / обязанности |
| `requirements` | `str` | Требования (может быть пустым) |
| `url` | `str` | Прямая ссылка на вакансию |
| `salary_from` | `int \| None` | Зарплата от (None если не указана) |
| `salary_to` | `int \| None` | Зарплата до (None если не указана) |
| `currency` | `str` | Валюта, например `"RUB"` |
| `published_at` | `datetime \| str \| None` | Дата публикации |

---

## Существующие источники

### hh.ru — активен

**Файл:** `src/infrastructure/external/hh_client.py`

**API:** `https://api.hh.ru/vacancies` — публичный, без авторизации.

**Поведение:**
- Две страницы параллельно (`page=0` и `page=1`, `per_page=50`) → до 100 вакансий
- Дедупликация по `id` перед возвратом
- Если результатов < 5 — автоматически повторяет без фильтра `experience=noExperience`
  (широкий поиск через `search_vacancies_broad`)
- Фильтры по умолчанию: `area=1` (Москва), `search_field=name`, `experience=noExperience`

**Маппинг специализации → поисковый запрос (`SPEC_TO_QUERY`):**
```python
"Финансы":    "финансовый аналитик"
"Консалтинг": "консультант аналитик"
"Маркетинг":  "маркетолог"
"HR":         "HR менеджер"
"Операции":   "операционный менеджер"
"IT":         "разработчик программист"
```

**Технические навыки, добавляемые в запрос (`TECH_SKILLS_FOR_QUERY`):**
`Excel`, `Python`, `SQL`, `Figma`, `PowerPoint` — до двух навыков из профиля.

**Маппинг schedule → WorkFormat:**
```python
"remote"      → WorkFormat.REMOTE
"fullDay"     → WorkFormat.OFFICE
"flexible"    → WorkFormat.HYBRID
"flyInFlyOut" → WorkFormat.OFFICE
```

**Дополнительные методы:**
- `get_vacancy(id)` — полные данные вакансии по ID
- `fetch_vacancy_by_url(url)` — парсит hh.ru/vacancy/123456 и возвращает domain Vacancy
- `parse_hh_url(url)` — статический метод, извлекает ID из URL (поддерживает spb.hh.ru, headhunter.ru)
- `vacancy_to_domain(raw)` — маппит сырой ответ API в domain Vacancy

---

### SuperJob — написан, не активен

**Файл:** `src/infrastructure/external/superjob_client.py`

**Причина отключения:** Нет API ключа. Получить: https://api.superjob.ru

**Как включить:** Добавить `SUPERJOB_API_KEY=...` в `.env`.
Клиент сам определяет наличие ключа: `self._enabled = bool(api_key)`.
При пустом ключе `search_vacancies()` возвращает `[]` без ошибок.

**API:** `https://api.superjob.ru/2.0/vacancies/`
Авторизация: заголовок `X-Api-App-Id: {api_key}`

**Параметры запроса:**
```python
{
    "keyword": query,
    "no_agreement": 1,  # только с указанной зарплатой (или стажировки)
    "count": 50,
    "town": 4,          # Москва
}
```

**Маппинг специализации (`SPEC_TO_QUERY_SJ`):**
```python
"Финансы":    "финансовый аналитик стажёр"
"Консалтинг": "консультант стажёр"
"Маркетинг":  "маркетолог стажёр"
"HR":         "HR стажёр"
"Операции":   "операционный менеджер стажёр"
"IT":         "программист стажёр"
```

**Поля маппинга из SuperJob API:**
```python
"profession"      → title
"firm_name"       → company
"town.title"      → city
"vacancyRichText" → description
"candidat"        → requirements
"link"            → url
"payment_from"    → salary_from
"payment_to"      → salary_to
"currency"        → currency (переводится в uppercase)
"date_published"  → published_at (Unix timestamp → datetime)
```

---

### Telegram-каналы — заглушка

**Файл:** `src/infrastructure/external/telegram_parser.py`

**Причина отключения:** Нет `TELEGRAM_API_ID` и `TELEGRAM_API_HASH`.
При их отсутствии `fetch_vacancies()` сразу возвращает `[]`.

**Как это работает (когда включено):**
Использует Telethon (MTProto) — не бот-токен, а полноценный клиент.
Читает последние `limit_per_channel=50` сообщений из каждого канала за `days=7` дней,
фильтрует по ключевым словам вакансий.

**Ключевые слова для фильтрации:**
```
стажировк, стажёр, intern, internship, junior, джуниор,
вакансия, набор, ищем, открыта позиция
```

**Нормализация:**
```python
"source_id": f"tg_{channel}_{message.id}"
"title":     первая непустая строка сообщения (до 120 символов)
"company":   f"@{channel}"
"url":       первый URL из текста или https://t.me/{channel}/{id}
"description": text[:3000]
```

**Список каналов** задаётся через `.env`:
```
TELEGRAM_CHANNELS=pmclub,budujobs,studreru,vrabote_me,vacanciesbest,Axenix_Ru,tedo_career,gpbcareer,ozoncamp,magnit_students,RSHB_CAREER,b1_careers,chernogolovka_profuture,avito_career,pmiru_job
```

---

## Как добавить новый источник вакансий

Пошаговая инструкция на примере добавления источника `ExampleSource`.

### Шаг 1: Создай клиент

`src/infrastructure/external/example_client.py`

```python
import logging
from typing import Any
import httpx
from src.core.config import settings

logger = logging.getLogger(__name__)

class ExampleClient:
    def __init__(self) -> None:
        api_key = settings.example.api_key          # добавь в config.py
        self._enabled = bool(api_key)
        self._client = httpx.AsyncClient(
            base_url="https://api.example.com",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0,
        )
        if not self._enabled:
            logger.info("EXAMPLE_API_KEY не задан — Example отключён")

    async def close(self) -> None:
        await self._client.aclose()

    async def search_vacancies(self, query: str) -> list[dict[str, Any]]:
        if not self._enabled:
            return []
        try:
            resp = await self._client.get("/vacancies", params={"q": query})
            resp.raise_for_status()
            items = resp.json().get("items", [])
            return [self._normalize(item) for item in items]
        except Exception as e:
            logger.error("Example search failed: %s", e)
            return []

    @staticmethod
    def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
        # Приводи к унифицированному формату агрегатора
        return {
            "source":      "example",
            "source_id":   str(raw.get("id", "")),
            "title":       raw.get("name", ""),
            "company":     raw.get("employer", ""),
            "city":        raw.get("city", ""),
            "description": raw.get("description", ""),
            "requirements": raw.get("requirements", ""),
            "url":         raw.get("url", ""),
            "salary_from": raw.get("salary_min"),
            "salary_to":   raw.get("salary_max"),
            "currency":    "RUB",
            "published_at": raw.get("created_at"),
        }
```

### Шаг 2: Добавь настройки в config.py

```python
# src/core/config.py
class ExampleSettings(BaseSettings):
    api_key: str = ""
    model_config = {"env_file": ".env", "env_prefix": "EXAMPLE_", "extra": "ignore"}

class Settings(BaseSettings):
    ...
    example: ExampleSettings = ExampleSettings()
```

### Шаг 3: Добавь в ContainerMiddleware

```python
# src/interface/telegram/middlewares/container.py
from src.infrastructure.external.example_client import ExampleClient

@dataclass
class Container:
    ...
    example_client: ExampleClient

class ContainerMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        ...
        self._example_client = ExampleClient()

    async def __call__(self, ...):
        container = Container(
            ...
            example_client=self._example_client,
        )
```

### Шаг 4: Добавь в VacancyAggregator

```python
# src/application/services/vacancy_aggregator.py
class VacancyAggregator:
    def __init__(self, hh_client, superjob_client, telegram_parser, example_client):
        ...
        self._example = example_client

    async def fetch_all(self, profile, hh_filters=None):
        ...
        example_task = asyncio.create_task(self._fetch_example(query))

        hh_results, sj_results, tg_results, example_results = await asyncio.gather(
            hh_task, sj_task, tg_task, example_task, return_exceptions=False
        )
        all_vacancies.extend(example_results)

    async def _fetch_example(self, query: str) -> list[dict]:
        try:
            return await self._example.search_vacancies(query)
        except Exception as e:
            logger.error("Example aggregation failed: %s", e)
            return []
```

### Шаг 5: Добавь маппинг специализации (опционально)

Если у источника есть своя логика поиска по специализации:
```python
# В клиенте или в aggregator.py
SPEC_TO_QUERY_EXAMPLE: dict[str, str] = {
    "Финансы":    "finance intern",
    "IT":         "developer intern",
    ...
}
```

### Шаг 6: Добавь ключ в .env.example

```bash
# .env.example
EXAMPLE_API_KEY=
```

### Шаг 7: Добавь VacancySource (если нужно хранить в БД)

```python
# src/domain/value_objects/vacancy_source.py
class VacancySource(str, Enum):
    HH_RU     = "hh_ru"
    SUPERJOB  = "superjob"
    TELEGRAM  = "telegram"
    MANUAL    = "manual"
    EXAMPLE   = "example"   # ← добавить
```

---

## Как настроить Telegram-парсер

Когда получите `api_id` и `api_hash` от https://my.telegram.org:

1. Добавьте в `.env`:
```
TELEGRAM_API_ID=1234567
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890
TELEGRAM_CHANNELS=pmclub,budujobs,studreru,vrabote_me
```

2. Установите `telethon` (добавить в `pyproject.toml`):
```toml
"telethon>=1.36.0",
```

3. При первом запуске Telethon запросит авторизацию через SMS/код.
Сессия сохраняется в файл `stazka_parser.session` рядом с точкой запуска.
Этот файл нужно добавить в `.gitignore` (уже добавлен).

4. В `docker-compose.yml` нужно примонтировать volume для файла сессии:
```yaml
bot:
  volumes:
    - ./stazka_parser.session:/app/stazka_parser.session
```

**Важно:** `api_id`/`api_hash` — это учётные данные вашего личного Telegram-аккаунта,
не бот-токен. Парсинг идёт от имени этого аккаунта.

---

## Matching Service — как вакансии ранжируются

После сбора из всех источников список попадает в `MatchingService`:

**L1 — Жёсткий фильтр** (`SPEC_KEYWORDS`):
Оставляет только вакансии, в тексте которых есть хотя бы одно ключевое слово
для специализации пользователя. Если специализация неизвестна — пропускает фильтр.

**L2 — Keyword scoring** (0–100):
```
Базовый score:              30
+10 за каждый навык из профиля, найденный в тексте
+15 за совпадение желаемой должности
+10 за совпадение города
+5 за совпадение специализации
Максимум:                  100
```

**L3 — Claude scoring** (top-40 параллельно):
Claude (модель `anthropic/claude-haiku-3-5-20251001`) получает текст вакансии и профиль,
возвращает `{"score": 0-100, "reason": "..."}`. При ошибке используется keyword_score.

**Финальный score:** `claude_score` если Claude ответил, иначе `keyword_score`.

Хендлер берёт первые 5 из отсортированного списка, остаток кэширует в FSM state
для кнопки «Показать ещё 5».
