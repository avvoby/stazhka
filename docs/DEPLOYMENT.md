# Деплой Стажки

## Сервер

| Параметр | Значение |
|----------|---------|
| Провайдер | Yandex Cloud VM |
| IP | 213.165.196.186 |
| Пользователь | avvoby |
| SSH ключ | `~/.ssh/ssh-key-1773246529615` |

## Подключение к серверу

```bash
ssh -i ~/.ssh/ssh-key-1773246529615 avvoby@213.165.196.186
```

---

## Первый деплой (с нуля)

### 1. Установить Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker avvoby && newgrp docker
```

### 2. Склонировать репозиторий

```bash
git clone https://github.com/avvoby/stazhka.git
cd stazhka
```

### 3. Создать .env файл

```bash
nano .env
```

Заполнить все переменные из `.env.example`:
```
TELEGRAM_BOT_TOKEN=...
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/stazhka
POSTGRES_USER=...
POSTGRES_DB=...
POSTGRES_PASSWORD=...
OPENROUTER_API_KEY=...
REDIS_URL=redis://redis:6379/0
CAREER_WEEK_ENABLED=true
CAREER_WEEK_ADMIN_IDS=[5645685337]
GOOGLE_SHEETS_ID=1cKE-HP2Lj3fMYcBcTCdJ4_F-FX-FWp-AvUEIMZPLb4A
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account",...}
```

### 4. Запустить

```bash
docker compose up -d db redis
docker compose --profile migrate up migrations --build
docker compose up -d --build bot
docker compose logs bot --tail=20
```

---

## Обновление (после изменений в коде)

**На Mac (локально):**
```bash
git add . && git commit -m "описание изменений" && git push
```

**На сервере:**
```bash
cd stazhka && git pull
docker compose up -d --build bot
```

### Если нужны новые миграции БД

```bash
docker compose --profile migrate up migrations --build
docker compose up -d --build bot
```

---

## Полезные команды на сервере

```bash
# Логи бота (последние 50 строк)
docker compose logs bot --tail=50

# Следить за логами в реальном времени
docker compose logs bot -f

# Статус всех контейнеров
docker compose ps

# Перезапустить только бота
docker compose restart bot

# Остановить всё
docker compose down

# Проверить место на диске
df -h

# Использование ресурсов контейнерами
docker stats
```

---

## Структура Docker Compose

```
bot         — aiogram polling + FastAPI + APScheduler (порт 8000)
db          — PostgreSQL 16 (порт 5432, данные в volume)
redis       — Redis 7 (порт 6379, данные в volume)
migrations  — Alembic (profile=migrate, запускается вручную)
```

Все контейнеры запущены с `restart: unless-stopped` —
автоматически поднимаются после перезагрузки сервера.

---

## Переменная GOOGLE_SERVICE_ACCOUNT_JSON

Это JSON service account из Google Cloud Console, сжатый в одну строку.

Как получить:
1. Google Cloud Console → IAM → Service Accounts → Create
2. Скачать JSON ключ
3. Сжать в одну строку: `python3 -c "import json,sys; print(json.dumps(json.load(open(sys.argv[1]))))" key.json`
4. Вставить в `.env` как значение `GOOGLE_SERVICE_ACCOUNT_JSON`
5. Дать сервисному аккаунту доступ к таблице (Editor или Viewer)

---

## Стоимость

| Компонент | Стоимость |
|-----------|----------|
| Yandex Cloud VM | ~800–1200 руб/мес |
| PostgreSQL | входит в VM |
| Redis | входит в VM |
| OpenRouter (Claude) | pay-per-token, ~$1–5/мес при умеренной нагрузке |

---

## Откат на предыдущую версию

```bash
# Посмотреть историю
git log --oneline -10

# Откатиться к конкретному коммиту
git checkout <commit_hash>
docker compose up -d --build bot

# Вернуться на main
git checkout main
```

> Миграции БД откатывать вручную через `alembic downgrade` если нужно.
