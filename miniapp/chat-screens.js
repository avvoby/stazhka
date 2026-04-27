/* Chat tab — C-1..C-12 */
window.Screens = (function(){
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

const ICON={
  back:'<svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg>',
  search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  send:'<svg viewBox="0 0 24 24"><path d="M3 12 21 3l-6 18-4-8z"/></svg>',
  attach:'<svg viewBox="0 0 24 24"><path d="M21 12.5 13 20a5 5 0 0 1-7-7l9-9a3.5 3.5 0 0 1 5 5l-9 9a2 2 0 0 1-3-3l8-8"/></svg>',
  dots:'<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/></svg>',
  bot:'<svg viewBox="0 0 24 24"><rect x="4" y="7" width="16" height="12" rx="3"/><path d="M9 12v2M15 12v2"/><path d="M12 3v4"/></svg>',
  sparkle:'<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5z"/><path d="M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8z"/></svg>',
  check2:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m3 12 4 4L14 7M9 16l4 4L21 9"/></svg>',
  check1:'<svg viewBox="0 0 24 24"><path d="M5 12l5 5L20 7"/></svg>',
  calendar:'<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></svg>',
  pin:'<svg viewBox="0 0 24 24"><path d="M12 2v7l4 4v2H8v-2l4-4V2zM12 15v7"/></svg>',
  mic:'<svg viewBox="0 0 24 24"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>',
  plus:'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  archive:'<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="4" rx="1"/><path d="M5 9v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V9M10 13h4"/></svg>',
};

/* ---------- Chat header ---------- */
function chatHeader(title, sub, avatar, color){
  return `
  <div class="chat-head">
    <button class="back" data-go="C-1">${ICON.back}</button>
    <div class="ch-av" style="background:${color||'var(--accent-2)'};color:${color?'#fff':'var(--accent)'}">${avatar}</div>
    <div class="ch-title">
      <div class="ch-name">${title}</div>
      <div class="ch-sub">${sub}</div>
    </div>
    <div class="ch-more">${ICON.dots}</div>
  </div>`;
}

/* ---------- Composer ---------- */
function composer(placeholder, quick, replyBar){
  return `
    ${replyBar||''}
    ${quick ? `<div class="quick-replies">${quick.map(q=>`<span class="qr" data-send="${esc(q)}">${esc(q)}</span>`).join('')}</div>`:''}
    <div class="composer">
      <div class="cp-attach">${ICON.attach}</div>
      <input class="cp-input" placeholder="${placeholder||'Сообщение'}"/>
      <div class="cp-send">${ICON.send}</div>
    </div>
  `;
}

/* Reusable bubbles */
const bubbleIn  = (t, time)=>`<div class="bubble in"><div class="b-body">${t}</div><div class="b-time">${time||''}</div></div>`;
const bubbleOut = (t, time, state)=>`<div class="bubble out"><div class="b-body">${t}</div><div class="b-time">${time||''} <span class="b-st">${state==='read'?ICON.check2:ICON.check1}</span></div></div>`;
const bubbleSys = (t)=>`<div class="b-sys"><span>${t}</span></div>`;

/* ================== C-1: Список чатов ================== */
const C1={id:'C-1',name:'Список чатов',render(s){
  const ROWS = [
    {to:'C-2', av:'★', color:'var(--accent)', name:'AI-наставник', sub:'Могу показать 3 новые вакансии под твой профиль. Посмотрим?', time:'14:02', unread:2, pinned:true, ai:true},
    {to:'C-5', av:'СК', color:'#0F4C7A', name:'HR · Сбер', sub:'Анна (Сбер): Здравствуйте! Спасибо за отклик…', time:'12:40', unread:1},
    {to:'C-6', av:'Я', color:'#2B2B2B', name:'HR · Яков и Партнёры', sub:'Приглашаем на интервью в среду 14:00', time:'вчера', hasCard:true},
    {to:'C-7', av:'VK', color:'#1E6E4A', name:'HR · VK', sub:'Вы: Спасибо, готов присоединиться', time:'вчера', read:true},
    {to:'C-8', av:'Т', color:'#FFCC00', name:'HR · Т-Банк', sub:'К сожалению, в этот раз не получилось…', time:'пн', rejected:true},
    {to:'', av:'М', color:'#888', name:'HR · McKinsey', sub:'Черновик сохранён', time:'вс', draft:true},
  ];
  return `
  <div class="screen active has-tabbar" data-id="C-1" style="padding:0">
    <div class="list-head">
      <div class="lh-top">
        <div class="lh-title">Чат</div>
        <div class="lh-new">${ICON.plus}</div>
      </div>
      <div class="lh-search">
        ${ICON.search}
        <input placeholder="Поиск по чатам" />
      </div>
    </div>
    <div class="chat-list">
      ${ROWS.map(r => `
        <div class="cl-row" ${r.to?`data-go="${r.to}"`:''}>
          <div class="cl-av" style="background:${r.color};color:#fff">${r.av}${r.ai?`<span class="cl-ai-dot"></span>`:''}</div>
          <div class="cl-body">
            <div class="cl-top">
              <div class="cl-name">
                ${r.pinned?`<span class="pin-ic">${ICON.pin}</span>`:''}
                ${esc(r.name)}
              </div>
              <div class="cl-time">${r.time}</div>
            </div>
            <div class="cl-bot">
              <div class="cl-sub ${r.draft?'draft':''} ${r.rejected?'rejected':''}">
                ${r.draft?'<span class="draft-tag">Черновик:</span> ':''}
                ${r.hasCard?'<span class="card-tag">📅 Слот</span> ':''}
                ${esc(r.sub)}
              </div>
              ${r.unread?`<span class="cl-badge">${r.unread}</span>`:r.read?`<span class="cl-read">${ICON.check2}</span>`:''}
            </div>
          </div>
        </div>`).join('')}

      <div class="cl-arch">
        <div class="cl-arch-ic">${ICON.archive}</div>
        <div>Архив · 3 чата</div>
      </div>
    </div>
  </div>`;
}};

/* ================== C-2: AI-наставник · активный диалог ================== */
const C2={id:'C-2',name:'AI · активный диалог',render(s){
  return `
  <div class="screen active chat" data-id="C-2" style="padding:0">
    ${chatHeader('AI-наставник','всегда онлайн · не человек','★','var(--accent)')}
    <div class="chat-scroll">
      ${bubbleSys('Сегодня')}
      ${bubbleIn('Привет! Я твой наставник по стажкам. Задавай вопросы про вакансии, помогу с резюме и подготовкой. С чего начнём?', '13:45')}
      ${bubbleOut('Какие сейчас хорошие стажировки в банках для 3 курса?','13:58','read')}
      ${bubbleIn(`Вот что есть на этой неделе (match под твой профиль > 75%):
      <div class="b-card vac">
        <div class="b-card-top"><div class="b-card-logo">С</div><div><div class="b-card-t">Сбер · Стажёр-аналитик</div><div class="b-card-sub">Москва · 60 000 ₽ · match 89%</div></div></div>
        <div class="b-card-tags"><span>SQL</span><span>Excel</span><span>финмодели</span></div>
        <div class="b-card-act">Открыть вакансию</div>
      </div>`,'14:00')}
      ${bubbleIn('Могу добавить ещё 2 варианта — Альфа и Т-Банк. Или разобрать конкретную вакансию детальнее.','14:00')}
      <div class="typing">
        <span></span><span></span><span></span>
      </div>
    </div>
    ${composer('Спроси меня о чём угодно', ['Покажи Альфу','Что спрашивают на интервью в Сбере?','Разбери моё резюме'])}
  </div>`;
}};

/* ================== C-3: AI · первый запуск (empty state) ================== */
const C3={id:'C-3',name:'AI · первый запуск',render(s){
  return `
  <div class="screen active chat" data-id="C-3" style="padding:0">
    ${chatHeader('AI-наставник','всегда онлайн · не человек','★','var(--accent)')}
    <div class="chat-empty">
      <div class="empty-hero">
        <div class="eh-bot">${ICON.bot}</div>
        <div class="eh-title">Спроси что угодно про стажки</div>
        <div class="eh-sub">Вакансии · резюме · подготовка к интервью. Работает 24/7, не человек — ответы мгновенные.</div>
      </div>
      <div class="empty-prompts">
        <div class="group-title" style="margin-top:0">Частые вопросы</div>
        <div class="prompt-card" data-send="Покажи 3 стажировки под мой профиль">
          <div class="pc-ic">${ICON.sparkle}</div>
          <div>
            <div class="pc-t">Подбери 3 стажировки под мой профиль</div>
            <div class="pc-s">AI посмотрит резюме и базу вакансий</div>
          </div>
        </div>
        <div class="prompt-card" data-send="Что чаще всего спрашивают на интервью в консалтинг?">
          <div class="pc-ic">${ICON.sparkle}</div>
          <div>
            <div class="pc-t">Что спрашивают на интервью в консалтинг</div>
            <div class="pc-s">Примеры вопросов, фреймворки, cases</div>
          </div>
        </div>
        <div class="prompt-card" data-send="Разбери моё резюме">
          <div class="pc-ic">${ICON.sparkle}</div>
          <div>
            <div class="pc-t">Разбери моё резюме</div>
            <div class="pc-s">Слабые места + 3 конкретных правки</div>
          </div>
        </div>
      </div>
    </div>
    ${composer('Спроси меня о чём угодно')}
  </div>`;
}};

/* ================== C-4: AI · набор ответа + tone-check ================== */
const C4={id:'C-4',name:'AI · tone-check при вводе',render(s){
  return `
  <div class="screen active chat" data-id="C-4" style="padding:0">
    ${chatHeader('AI-наставник','всегда онлайн · не человек','★','var(--accent)')}
    <div class="chat-scroll">
      ${bubbleIn('Могу помочь с cover letter для Сбера. Кинь мне текст, который хочешь отправить — проверю тон.','14:10')}
    </div>
    <div class="typing-tip">
      <div class="tt-label">${ICON.sparkle} AI заметил</div>
      <div class="tt-body">Слишком формально для Сбера — они сейчас ищут «своих ребят». Стоит смягчить и убрать «имею честь».</div>
      <div class="tt-act"><span class="tt-btn">Переписать</span><span class="tt-btn ghost">Оставить как есть</span></div>
    </div>
    <div class="composer draft">
      <div class="cp-attach">${ICON.attach}</div>
      <div class="cp-input typed">Уважаемые коллеги, имею честь направить вам своё резюме на позицию стажёра-аналитика и надеюсь на положительное рассмотрение…</div>
      <div class="cp-send active">${ICON.send}</div>
    </div>
  </div>`;
}};

/* ================== C-5: HR Сбер · новый входящий ================== */
const C5={id:'C-5',name:'HR Сбер · первое сообщение',render(s){
  return `
  <div class="screen active chat" data-id="C-5" style="padding:0">
    ${chatHeader('Анна · HR Сбер','СберБанк · был(а) в сети сейчас','СК','#0F4C7A')}
    <div class="chat-scroll">
      ${bubbleSys('Пятница · 12:40')}
      ${bubbleIn('Здравствуйте, Иван! Меня зовут Анна, я из команды подбора Сбера. Спасибо за отклик на стажку аналитика.','12:40')}
      ${bubbleIn('Могли бы вы ответить на пару коротких вопросов — это займёт 5 минут:<br><br>1. В каком формате хотели бы стажироваться — офис / гибрид?<br>2. Когда готовы начать?','12:41')}

      <div class="ai-hint">
        <div class="ah-lbl">${ICON.sparkle} Подсказка Стажки</div>
        <div class="ah-body">Анна оценивает тон и скорость. Ответь развёрнуто, но по сути — 2-3 предложения.</div>
      </div>
    </div>
    ${composer('Ответьте Анне', ['Готов начать с 15 октября','Гибрид предпочтителен','Могу уточнить дату завтра'])}
  </div>`;
}};

/* ================== C-6: HR Яков · приглашение на интервью (карточка-слот) ================== */
const C6={id:'C-6',name:'HR · слот интервью',render(s){
  return `
  <div class="screen active chat" data-id="C-6" style="padding:0">
    ${chatHeader('Елена · Яков и Партнёры','строгий дресс-код · SBS','Я','#2B2B2B')}
    <div class="chat-scroll">
      ${bubbleSys('вчера')}
      ${bubbleIn('Иван, добрый день! Ваше резюме прошло скрининг. Приглашаем на очное кейс-интервью.','16:02')}
      ${bubbleIn(`
        <div class="b-card slot">
          <div class="b-card-top">
            <div class="b-card-logo" style="background:#2B2B2B;color:#fff">${ICON.calendar}</div>
            <div>
              <div class="b-card-t">Кейс-интервью · 45 мин</div>
              <div class="b-card-sub">среда, 9 октября · 14:00</div>
            </div>
          </div>
          <div class="slot-grid">
            <div><b>Формат</b><span>очное в офисе</span></div>
            <div><b>Адрес</b><span>Лесная 7, эт. 5</span></div>
            <div><b>Интервьюер</b><span>Пётр Н., Partner</span></div>
            <div><b>Подготовка</b><span>Profitability case</span></div>
          </div>
          <div class="slot-act">
            <span class="sa-btn primary">Подтвердить</span>
            <span class="sa-btn ghost">Предложить другое время</span>
          </div>
        </div>`,'16:03')}

      <div class="ai-hint link">
        <div class="ah-lbl">${ICON.sparkle} Стажка</div>
        <div class="ah-body">Подготовлю к profitability-кейсу — <a href="Stazhka Prep.html">открыть тренинг</a>. Добавлю интервью в твой трекер автоматически.</div>
      </div>
    </div>
    ${composer('Напишите Елене',['Подтверждаю, буду в 14:00','Спасибо, готов к кейсу'])}
  </div>`;
}};

/* ================== C-7: HR · после подтверждения (quick replies от AI) ================== */
const C7={id:'C-7',name:'HR · после подтверждения',render(s){
  return `
  <div class="screen active chat" data-id="C-7" style="padding:0">
    ${chatHeader('Сергей · VK','Холдинг VK · online','VK','#1E6E4A')}
    <div class="chat-scroll">
      ${bubbleIn('Здравствуйте! Рады пригласить вас на финальный этап — встреча с тимлидом и тех-директором, 40 минут.','14:15')}
      ${bubbleIn('Готовы в четверг 10 октября, 11:30?','14:15')}
      ${bubbleOut('Да, подтверждаю! Буду в 11:30','14:18','read')}
      ${bubbleIn('Отлично. Ссылка на Zoom придёт за час до встречи.','14:22')}
      ${bubbleOut('Спасибо, готов присоединиться','14:25','read')}
    </div>
    <div class="ai-quick-bar">
      <div class="aqb-lbl">${ICON.sparkle} Стажка готовит варианты</div>
      <div class="aqb-chips">
        <span class="aqb-chip">Можно заранее уточнить темы?</span>
        <span class="aqb-chip">Нужна ли презентация?</span>
        <span class="aqb-chip">Спасибо, буду готовиться</span>
      </div>
    </div>
    ${composer('Написать Сергею')}
  </div>`;
}};

/* ================== C-8: HR · отказ + эмпатия AI ================== */
const C8={id:'C-8',name:'HR · отказ',render(s){
  return `
  <div class="screen active chat" data-id="C-8" style="padding:0">
    ${chatHeader('Ольга · Т-Банк','Желтый банк · была в сети 2 ч назад','Т','#FFCC00')}
    <div class="chat-scroll">
      ${bubbleSys('понедельник · 10:21')}
      ${bubbleIn('Иван, здравствуйте. К сожалению, в этот раз не получилось — команда выбрала другого кандидата. Вы дошли до финала, это сильный результат.','10:21')}
      ${bubbleIn('Если интересно — готова дать короткий фидбек по интервью. Напишите, если нужно.','10:22')}

      <div class="ai-hint big">
        <div class="ah-lbl">${ICON.sparkle} Стажка рядом</div>
        <div class="ah-body">Отказ после финала — это больно, но значит ты близко. Давай разберём фидбек вместе и сохраним в дневник — пригодится для следующего интервью.</div>
        <div class="ah-act">
          <a class="ah-btn primary" href="Stazhka Search.html#S-9a">Открыть дневник отказов</a>
          <span class="ah-btn ghost">Не сейчас</span>
        </div>
      </div>
    </div>
    ${composer('Ответить Ольге', ['Да, буду благодарен за фидбек','Спасибо, было полезно'])}
  </div>`;
}};

/* ================== C-9: AI · follow-up напоминание ================== */
const C9={id:'C-9',name:'AI · напоминание о фоллоу-апе',render(s){
  return `
  <div class="screen active chat" data-id="C-9" style="padding:0">
    ${chatHeader('AI-наставник','всегда онлайн · не человек','★','var(--accent)')}
    <div class="chat-scroll">
      ${bubbleSys('сегодня · 09:30')}
      ${bubbleIn(`
        Анна из Сбера не отвечала 3 рабочих дня. Это нормально, у HR очереди. Обычно вежливый фоллоу-ап увеличивает ответы на 28%.
        <div class="b-card hint">
          <div class="b-card-top">
            <div class="b-card-logo" style="background:#0F4C7A;color:#fff">СК</div>
            <div>
              <div class="b-card-t">Написать Анне (Сбер)</div>
              <div class="b-card-sub">последний контакт · пятница</div>
            </div>
          </div>
          <div class="b-card-quote">
            «Добрый день, Анна! Подскажите, пожалуйста, есть ли обновление по моей кандидатуре? Готов уточнить любые детали. Спасибо!»
          </div>
          <div class="b-card-act-row">
            <span class="bc-btn primary">Отправить</span>
            <span class="bc-btn ghost">Отредактировать</span>
          </div>
        </div>
      `,'09:30')}
    </div>
    ${composer('Ответить AI',['Отправь как есть','Напомни завтра','Пропустить'])}
  </div>`;
}};

/* ================== C-10: HR · прикрепление файла ================== */
const C10={id:'C-10',name:'HR · файлы',render(s){
  return `
  <div class="screen active chat" data-id="C-10" style="padding:0">
    ${chatHeader('Анна · HR Сбер','СберБанк · online','СК','#0F4C7A')}
    <div class="chat-scroll">
      ${bubbleIn('Иван, отправьте, пожалуйста, актуальное резюме в PDF.','13:05')}
      ${bubbleOut(`
        <div class="b-file">
          <div class="b-file-ic">PDF</div>
          <div class="b-file-body">
            <div class="b-file-name">Иванов_резюме_окт2024.pdf</div>
            <div class="b-file-size">142 КБ · 1 страница</div>
          </div>
        </div>
      `,'13:12','read')}
      ${bubbleOut('Отправил. Если нужно в другом формате — скажите.','13:12','read')}
      ${bubbleIn('Получила, спасибо. Передаю команде — вернусь с фидбеком в течение 2 рабочих дней.','13:25')}

      <div class="ai-hint">
        <div class="ah-lbl">${ICON.sparkle} Резюме переписки</div>
        <div class="ah-body">HR Сбера получил резюме. Фидбек ожидается до среды — добавил напоминание в трекер.</div>
      </div>
    </div>
    <div class="attach-bar">
      <div class="ab-item">
        <div class="ab-ic">📄</div><div>Резюме PDF</div>
      </div>
      <div class="ab-item">
        <div class="ab-ic">📂</div><div>Из профиля</div>
      </div>
      <div class="ab-item">
        <div class="ab-ic">📎</div><div>Файл</div>
      </div>
    </div>
    ${composer('Сообщение')}
  </div>`;
}};

/* ================== C-11: AI · карточка вакансии и переход в поиск ================== */
const C11={id:'C-11',name:'AI · карточка → поиск',render(s){
  return `
  <div class="screen active chat" data-id="C-11" style="padding:0">
    ${chatHeader('AI-наставник','всегда онлайн · не человек','★','var(--accent)')}
    <div class="chat-scroll">
      ${bubbleOut('Покажи что-то в консалтинге с удалёнкой','11:04','read')}
      ${bubbleIn('Вот 3 варианта, которые подходят. Первая самая горячая — дедлайн через 5 дней:','11:04')}
      ${bubbleIn(`
        <div class="b-card vac warm">
          <div class="b-card-logo-wrap"><div class="b-card-logo">БКГ</div><div class="warm-badge">горячо</div></div>
          <div class="b-card-t">BCG · Intern, Practice Group</div>
          <div class="b-card-sub">удалённо · до 15 окт · match 84%</div>
          <div class="b-card-tags"><span>PowerPoint</span><span>SQL база</span><span>английский</span></div>
          <div class="b-card-row">
            <a class="bc-btn primary" href="Stazhka Search.html#S-5">Открыть</a>
            <span class="bc-btn ghost">Позже</span>
          </div>
        </div>
        <div class="b-card vac compact"><div class="b-card-t">McKinsey · Intern</div><div class="b-card-sub">удалённо · match 78%</div></div>
        <div class="b-card vac compact"><div class="b-card-t">Bain · Associate Intern</div><div class="b-card-sub">гибрид · match 71%</div></div>
      `,'11:04')}
      ${bubbleIn('Хочешь, оформлю отклик на BCG прямо сейчас? Подтяну твоё резюме и напишу cover letter.','11:05')}
    </div>
    ${composer('Ответить AI',['Да, оформи отклик','Сначала разбери BCG','Покажи ещё вакансии'])}
  </div>`;
}};

/* ================== C-12: Меню чата (long-press) ================== */
const C12={id:'C-12',name:'Меню чата',render(s){
  return `
  <div class="screen active has-tabbar" data-id="C-12" style="padding:0">
    <div class="list-head" style="filter:brightness(.92)">
      <div class="lh-top">
        <div class="lh-title">Чат</div>
        <div class="lh-new">${ICON.plus}</div>
      </div>
      <div class="lh-search" style="opacity:.5">
        ${ICON.search}
        <input placeholder="Поиск по чатам" disabled/>
      </div>
    </div>
    <div class="chat-list" style="filter:brightness(.92)">
      <div class="cl-row selected">
        <div class="cl-av" style="background:#0F4C7A;color:#fff">СК</div>
        <div class="cl-body">
          <div class="cl-top"><div class="cl-name">HR · Сбер</div><div class="cl-time">12:40</div></div>
          <div class="cl-bot"><div class="cl-sub">Анна (Сбер): Здравствуйте! Спасибо за отклик…</div></div>
        </div>
      </div>
    </div>

    <div class="bottom-sheet chat-menu">
      <div class="sheet-grab"></div>
      <div class="sm-act"><div class="sm-ic">📌</div><div class="sm-l">Закрепить чат</div></div>
      <div class="sm-act"><div class="sm-ic">🔕</div><div class="sm-l">Отключить уведомления</div></div>
      <div class="sm-act"><div class="sm-ic">${ICON.sparkle}</div><div class="sm-l">Пересказать от AI</div><div class="sm-r">новое</div></div>
      <div class="sm-act"><div class="sm-ic">${ICON.archive}</div><div class="sm-l">В архив</div></div>
      <div class="sm-act danger"><div class="sm-ic">🗑</div><div class="sm-l">Удалить чат</div></div>
      <div class="sm-cancel" data-go="C-1">Отмена</div>
    </div>
  </div>`;
}};

return [C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, C11, C12];
})();
