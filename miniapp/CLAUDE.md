# CLAUDE.md — Стажка Mini App

## Что это

Telegram Mini App для студентов ВШБ НИУ ВШЭ — фронт продукта «Стажка»: онбординг, поиск стажировок, подготовка к отбору, трекер откликов, AI-наставник, профиль.

Бэкенд (Python aiogram-бот) живёт отдельно: `/Users/Kirill/Developer/stazhka/`. Этот репо — только Mini App.

## Стек

- Vanilla HTML/CSS/JS. Никаких фреймворков (React/Vue/Svelte) и сборщиков (webpack/vite/ts).
- Только статика — GitHub Pages отдаёт как есть.
- AI-чат (этап 5): Cloudflare Worker → Anthropic API (`claude-haiku-4-5-20251001`).

## Архитектура

```
index.html              # Точка входа SPA
tg-app.js               # Shell-роутер: hash → секция → screen
tg-shell.css            # Стили обёртки (табы, splash)
store.js                # Единый стор (localStorage stazhka.state.v1)

proto-shell.css         # Дизайн-система (компоненты, токены)
chat.css                # Стили AI-чата

# 6 секций — каждая = engine + screens:
proto-engine.js + proto-screens.js          # Onboarding
search-engine.js + search-screens.js        # Поиск стажировок
prep-engine.js + prep-screens.js            # Подготовка
progress-engine.js + progress-screens.js    # Прогресс / трекер
chat-engine.js + chat-screens.js            # AI-наставник
profile-engine.js + profile-screens.js      # Профиль

worker/                 # Cloudflare Worker для AI-прокси (этап 5)
```

Каждый `*-screens.js` — массив `{id, render(state), bind?(root, state, api)}`.
Каждый `*-engine.js` — мини-роутер по хешу `#<section>/<screenId>[/<param>]`, рендерит активный экран в `<main id="stage">`.

## Стор

Единый ключ `stazhka.state.v1` в localStorage. Структура:

```js
{
  user:     { fio, course, program, direction, companies[], skills_score{excel,python,cases} },
  search:   { favorites[], hidden[], alerts[], applications[] },
  prep:     { hardSkills[], extraSkills, currentTrack, completedModules[] },
  progress: { points, streak, badges[] },
  profile:  { notifications, privacy },
  meta:     { onboardingDone, schemaVersion: 1, createdAt }
}
```

API: `Store.get()`, `Store.update(patch)`, `Store.subscribe(fn)`, `Store.reset()`.

Транзитное UI-состояние (текущий экран, фазы заявки, выбранный таб внутри секции) — НЕ в сторе, живёт в замыкании движка.

## Дизайн-токены (proto-shell.css)

Светлая тема, акцент тёплый красный.

```
--accent:   #7A1B1B
--ink:      #1C1C1E   (основной текст)
--ink-2:    #8E8E93   (вторичный)
--line:     #E5E5EA   (разделители)
--surface-2:#F5F5F7   (фон input/карточек)
bg:         #FFFFFF
```

Шрифт: системный (`-apple-system, SF Pro, Inter`). Все цифры (суммы, проценты, даты, статус-чипы uppercase) — в моноширинном начертании через класс `.mono-l` / `.mono-s`.

Радиусы: 3px кнопки, 4px карточки, 8px модальные. Бордеры 1px solid, без drop-shadow.

## Правила

- **Русский везде.** Никакого lorem ipsum, никаких placeholder-строк на английском.
- **Без эмоджи.** Ни в UI, ни в коммитах. Иконки — inline SVG (Lucide stroke 1.5–1.8).
- **Числа форматировать с пробелами** как разделителями тысяч: `1 142 300`. Даты на июнь–июль 2026.
- **Touch targets ≥ 44px.** Telegram это проверяет на iOS.
- **Только dark... нет, только light.** Не вводить тёмную тему без явного запроса.
- **`tg.themeParams` игнорируем.** Форсим свою фиксированную тему.
- **Не трогать**: цветовую палитру, шрифты, тип-сетку без явного запроса.
- **Никакого бэкенд-БД** (Supabase/Firebase) — всё в localStorage.
- **Никаких тестов** — это прототип для теста среди знакомых.
- **Консервативные правки.** Не переписывать работающие экраны без причины. Стор — оборачивает рендер, не выкидывает.

## Telegram WebApp SDK

- `tg.MainButton` — primary CTA каждого экрана. Движок объявляет `screen.mainButton = {text, onClick}`, shell ставит/прячет.
- `tg.BackButton` — на корне таба `hide()`, внутри (есть `screenId` в хеше) `show()` + клик = `history.back()`.
- `tg.HapticFeedback.impactOccurred('light')` — тапы по карточкам/чипам/табам.
- `tg.initDataUnsafe.user` — префилл `user.fio` при первом запуске.
- `tg.colorScheme` — только лог. `themeParams` — игнор.
- `tg.setHeaderColor('#7A1B1B')`, `tg.setBackgroundColor('#ffffff')` — фиксированно.

## Коммиты

Формат: `feat: …` / `fix: …` / `refactor: …` / `chore: …` на русском.

## Этапы рефакторинга (план, апрель 2026)

- [x] **0.** Репо `stazhka-miniapp/`, baseline-коммит
- [x] **1.** `store.js` — единый стор, миграция со старых ключей
- [x] **2.** Single-HTML SPA (убрать iframe, hash-роутер)
- [x] **3.** Telegram SDK (MainButton/BackButton/Haptic/initDataUnsafe)
- [ ] **4.** Сократить онбординг 10→5 экранов
- [ ] **5.** AI-чат через Cloudflare Worker
- [ ] **6.** Деплой на GitHub Pages + BotFather
