# Стажка — Telegram Mini App: deploy за 10 минут

Цель: получить публичный HTTPS-URL и привязать к боту `@stazhka_test_bot`, чтобы скидывать тестерам ссылку `t.me/stazhka_test_bot/app`.

## Шаг 1 — выкачать проект

В этом редакторе: меню «Скачать» → загрузить ZIP всего проекта. Распаковать локально.

Должны быть файлы:
- `index.html` (точка входа Mini App)
- `tg-app.js`, `tg-shell.css`
- `Stazhka *.html` (6 разделов)
- `*-engine.js`, `*-screens.js`, `proto-shell.css`

## Шаг 2 — задеплоить на GitHub Pages (бесплатно, HTTPS)

```bash
# в распакованной папке
git init
git add .
git commit -m "stazhka mini app"
# создать репозиторий stazhka на github.com (public)
git remote add origin https://github.com/<your-username>/stazhka.git
git branch -M main
git push -u origin main
```

На GitHub:
- Repository → **Settings** → **Pages**
- Source: `Deploy from a branch`
- Branch: `main` / `/ (root)` → **Save**

Через ~1 минуту получишь URL: `https://<your-username>.github.io/stazhka/`

Открой его в браузере — должна открыться «Стажка», табы снизу работают.

### Альтернатива: Cloudflare Pages

- Зайти на pages.cloudflare.com → Create project → Connect to Git → выбрать репо
- Build command: пусто; Output directory: `/`
- Получишь `https://stazhka.pages.dev`

Cloudflare обновляется быстрее (за 30 сек после `git push`).

## Шаг 3 — создать Mini App в BotFather

В Telegram открыть `@BotFather`:

```
/myapps
```

Выбрать `@stazhka_test_bot` → **Create New App**:
- **Title**: Стажка
- **Short name**: app  *(будет в URL: t.me/stazhka_test_bot/app)*
- **Description**: Поиск стажировок и подготовка к собесам
- **Photo / Icon**: 640×360 / 192×192 — любая картинка
- **Web App URL**: вставить URL из Шага 2 (`https://<username>.github.io/stazhka/`)

Готово. Mini App доступна по `https://t.me/stazhka_test_bot/app`.

## Шаг 4 — добавить кнопку запуска в боте (опционально)

Так запуск удобнее: не нужно слать ссылку, открывается из меню чата.

```
/mybots → @stazhka_test_bot → Bot Settings → Menu Button
```

Установить:
- Button text: `Открыть Стажку`
- URL: `https://t.me/stazhka_test_bot/app`

## Шаг 5 — раздать ссылку

Скинуть друзьям одну из:
- `https://t.me/stazhka_test_bot/app` — открывается прямо в Telegram
- `https://t.me/stazhka_test_bot` — открыть бот, потом тапнуть Menu Button

## Важно при тестировании

- **Данные в localStorage**: каждый тестер видит свой проект; данные не синхронизируются между устройствами. Это ОК для теста.
- **Сброс**: тестер может сбросить онбординг, очистив localStorage в Telegram (Settings → Advanced → Clear cache в desktop клиенте).
- **iOS**: в первый раз Telegram может закешировать старую версию — попроси тестера закрыть мини-апп и открыть заново.
- **Обновление кода**: после `git push` на GitHub Pages — обновится через 1–3 мин. На iOS придётся «long-press на Menu Button → Refresh» либо переоткрыть.

## Бэкенд через ngrok (для AI-чата)

Mini App статичен — фронт раздаёт GitHub Pages. Но AI-чат (раздел «Чат» → «AI-наставник») должен ходить на твой бэкенд (Python aiogram-бот в `/Users/Kirill/Developer/stazhka/`, FastAPI на `localhost:8000`). Telegram умеет открывать только HTTPS-адреса, значит локальный uvicorn нужно прокинуть наружу.

### Шаг A — поднять бэкенд

```bash
cd /Users/Kirill/Developer/stazhka
docker compose up -d api db redis
# логи: docker compose logs -f api
# проверка: curl http://localhost:8000/api/health
```

`OPENROUTER_API_KEY` должен быть в `.env` (он там уже).

### Шаг B — туннель ngrok с фиксированным доменом

ngrok даёт один бесплатный статичный домен на аккаунт. URL не меняется при перезапуске — это важно, потому что он зашит в `miniapp/index.html` и пушится в Pages.

1. **Установить**: https://ngrok.com/download → `brew install ngrok` (на macOS)
2. **Зарегистрироваться** на ngrok.com (бесплатно)
3. **Authtoken**: ngrok dashboard → Your Authtoken → скопировать → `ngrok config add-authtoken <TOKEN>`
4. **Reserved domain**: dashboard → Universal Gateway → Domains → New Domain. Получишь что-то вроде `https://stazhka-<суффикс>.ngrok-free.app` (бесплатно, до 1 домена на аккаунт)
5. **Запустить туннель**:
   ```bash
   ngrok http --domain=stazhka-<суффикс>.ngrok-free.app 8000
   ```
   Окно терминала должно остаться открытым. Закроешь — туннель упадёт.
6. **Проверить**: открой `https://stazhka-<суффикс>.ngrok-free.app/api/health` в браузере → должен вернуть JSON `{"status":"ok",...}`

### Шаг C — вписать URL в Mini App

Открой `miniapp/index.html`, найди:

```js
window.STAZHKA_CONFIG = {
  apiUrl: ''
};
```

Замени на свой:

```js
window.STAZHKA_CONFIG = {
  apiUrl: 'https://stazhka-<суффикс>.ngrok-free.app'
};
```

`git add miniapp/index.html && git commit -m "chore: api url" && git push origin main`. Через 1-3 мин Pages обновится → Mini App начнёт ходить в твой бэкенд.

### Что увидит юзер

- В разделе «Чат» → «AI-наставник» (карточка со звездой ★ сверху списка) — реальный диалог с Claude через OpenRouter (`claude-haiku-3-5`).
- Лимит: **5 запросов в день на Telegram-юзера**, in-memory счётчик в FastAPI (сбрасывается при рестарте `api`-контейнера). Для прода — переехать на Redis (есть скелет в `src/infrastructure/ai/rate_limiter.py`).
- Если `apiUrl` пустой или туннель лежит — Mini App покажет ошибку в чате, остальные секции работают как обычно.

### Туннель упал, что делать

- ngrok закрыл окно → запусти команду снова, домен тот же
- Mac уснул → разбуди, поправь сеть
- Хочешь мониторить uptime — навесь `caffeinate -d -i ngrok ...` или вынеси на VPS

## Troubleshooting

**Открывается, но видна странная белая полоса сверху** — нормально, это header Telegram. Цвет задаём в `tg-app.js` через `tg.setHeaderColor`.

**Кнопка «Назад» в Telegram-баре ничего не делает** — мы пытаемся нажать back-кнопку внутри секции; если её нет, переключает на «Поиск» / закрывает приложение.

**Старая версия после деплоя** — добавь к URL `?v=2` для cache-bust, либо обнови `index.html` (любая правка сбрасывает кеш Service Worker).
