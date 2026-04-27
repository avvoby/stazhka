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

## Troubleshooting

**Открывается, но видна странная белая полоса сверху** — нормально, это header Telegram. Цвет задаём в `tg-app.js` через `tg.setHeaderColor`.

**Кнопка «Назад» в Telegram-баре ничего не делает** — мы пытаемся нажать back-кнопку внутри секции; если её нет, переключает на «Поиск» / закрывает приложение.

**Старая версия после деплоя** — добавь к URL `?v=2` для cache-bust, либо обнови `index.html` (любая правка сбрасывает кеш Service Worker).
