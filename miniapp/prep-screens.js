/* ============================================================
   Stazhka Prep tab — screens (P-1 ... P-10b)
   ============================================================ */

window.Screens = (function(){

function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

const ICON = {
  back:'<svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg>',
  chev:'<svg viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>',
  check:'<svg viewBox="0 0 24 24"><path d="M5 12l4 4L19 7"/></svg>',
  lock:'<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>',
  play:'<svg viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M8 5v14l11-7z"/></svg>',
  mic:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>',
  search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  article:'<svg viewBox="0 0 24 24"><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 9h8M8 13h8M8 17h5"/></svg>',
  sheet:'<svg viewBox="0 0 24 24"><path d="M6 3h9l5 5v13a0 0 0 0 1 0 0H6a0 0 0 0 1 0 0V3z"/><path d="M15 3v5h5"/></svg>',
  video:'<svg viewBox="0 0 24 24"><rect x="3" y="6" width="14" height="12" rx="2"/><path d="m17 10 4-2v8l-4-2"/></svg>',
  calendar:'<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="16" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/></svg>',
  target:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none"/></svg>',
};

/* ---------- Data ---------- */
const TRACKS = [
  {id:'case', title:'Кейс-интервью', sub:'Структура, MECE, практика', total:12, done:4, accent:'case'},
  {id:'hr', title:'HR-скрининг', sub:'Почему компания, about me, слабые стороны', total:8, done:6, accent:'hr'},
  {id:'tests', title:'Тестовые задания', sub:'Excel, SQL, Python для стажёра', total:10, done:2, accent:'tests'},
  {id:'eng', title:'Английский для интервью', sub:'Small-talk, vocabulary, mock-разговор', total:6, done:0, accent:'eng'},
];

const CASE_MODULES = [
  {id:'c1', title:'Что такое case-интервью', meta:'Статья · 6 мин', state:'done'},
  {id:'c2', title:'Принцип MECE', meta:'Видео + квиз · 12 мин', state:'done'},
  {id:'c3', title:'Декомпозиция задачи', meta:'Статья · 10 мин', state:'done'},
  {id:'c4', title:'Market sizing: базовые приёмы', meta:'Видео · 8 мин', state:'done'},
  {id:'c5', title:'AI-тренажёр: «Сколько лифтов в Москве»', meta:'Практика · 15 мин', state:'current'},
  {id:'c6', title:'Profitability framework', meta:'Статья + пример · 12 мин', state:'open'},
  {id:'c7', title:'M&A кейсы', meta:'Видео · 14 мин', state:'locked'},
  {id:'c8', title:'Mock-интервью с AI', meta:'Практика · 25 мин', state:'locked'},
];

const LIBRARY = [
  {id:'l1', kind:'article', title:'Как отвечать на «расскажи о себе»', meta:'Статья · 5 мин'},
  {id:'l2', kind:'sheet',   title:'Шпаргалка: формулы Excel для стажёра', meta:'PDF · 2 стр'},
  {id:'l3', kind:'video',   title:'Разбор кейса McKinsey: розничный банк', meta:'Видео · 18 мин'},
  {id:'l4', kind:'article', title:'Слабые стороны: 10 вариантов ответа', meta:'Статья · 7 мин'},
  {id:'l5', kind:'sheet',   title:'SQL-шпаргалка: JOIN, GROUP BY, оконные', meta:'PDF · 3 стр'},
  {id:'l6', kind:'video',   title:'Как структурировать ответ по STAR', meta:'Видео · 9 мин'},
];

const PLAN_TASKS = [
  {id:'t1', label:'Пройти модуль «Profitability framework»', meta:'Подготовка · 12 мин', done:true},
  {id:'t2', label:'AI-тренажёр: market sizing (3 задачи)', meta:'Практика · 30 мин', done:true},
  {id:'t3', label:'Прочитать шпаргалку по SQL', meta:'Библиотека · 10 мин', done:false},
  {id:'t4', label:'Mock-интервью: HR-блок', meta:'Подготовка · 20 мин', done:false},
];

const MOCK_QUESTIONS = [
  'Расскажи о себе за 2 минуты',
  'Почему именно наша компания?',
  'Приведи пример, когда ты работал в команде и столкнулся с конфликтом',
];

/* =====================================================================
   P-1: Главная Подготовки
   ===================================================================== */
const P1 = {
  id:'P-1', name:'Подготовка · главная',
  render(s){
    const totalDone = TRACKS.reduce((a,t)=>a+t.done,0);
    const totalAll = TRACKS.reduce((a,t)=>a+t.total,0);
    return `
    <div class="screen active has-tabbar" data-id="P-1">
      <div class="screen-header">
        <div class="h-title">Подготовка</div>
        <div class="h-action" data-go="P-9" title="План на неделю">${ICON.calendar}</div>
      </div>
      <div class="screen-scroll">
        <div class="rec" data-go="P-4">
          <div class="rec-label">Рекомендовано сегодня</div>
          <div class="rec-title">AI-тренажёр: «Сколько лифтов в Москве»</div>
          <div class="rec-meta">Трек «Кейс-интервью» · 15 мин · следующий шаг в твоём плане</div>
        </div>

        <div style="font-size:11.5px;color:var(--ink-2);letter-spacing:.3px;margin-top:4px">
          ${totalDone} из ${totalAll} модулей пройдено
        </div>

        ${TRACKS.map(t=>{
          const pct = Math.round(t.done/t.total*100);
          return `
          <div class="track" data-track="${t.id}">
            <div class="t-top">
              <div>
                <div class="t-title">${esc(t.title)}</div>
                <div class="t-sub">${esc(t.sub)}</div>
              </div>
              <div class="t-pct">${pct}%</div>
            </div>
            <div class="bar"><span style="width:${pct}%"></span></div>
            <div class="t-sub" style="font-size:11.5px">${t.done}/${t.total} модулей</div>
          </div>`;
        }).join('')}

        <button class="btn ghost" data-go="P-7" style="margin-top:4px">Библиотека материалов</button>
        <button class="btn outline" data-go="P-10">Mock-интервью (3 вопроса)</button>
      </div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelectorAll('[data-track]').forEach(el=>{
      el.addEventListener('click', ()=>{
        s.currentTrack = el.dataset.track;
        a.goTo('P-2');
      });
    });
  }
};

/* =====================================================================
   P-2: Трек «Кейс-интервью»
   ===================================================================== */
const P2 = {
  id:'P-2', name:'Трек кейс-интервью',
  render(s){
    const track = TRACKS.find(t=>t.id===(s.currentTrack||'case')) || TRACKS[0];
    const pct = Math.round(track.done/track.total*100);
    return `
    <div class="screen active has-tabbar" data-id="P-2">
      <div class="s-head">
        <button class="back" data-go="P-1">${ICON.back}</button>
        <div class="pill">Трек · ${esc(track.title)}</div>
      </div>
      <div class="title">${esc(track.title)}</div>
      <div class="subtitle">${esc(track.sub)}</div>
      <div class="bar" style="margin:4px 0 14px;height:4px;background:var(--surface-2);border-radius:2px;overflow:hidden">
        <span style="display:block;height:100%;width:${pct}%;background:var(--accent)"></span>
      </div>
      <div class="screen-scroll">
        ${CASE_MODULES.map(m=>{
          const cls = m.state==='done' ? 'done' : m.state==='locked' ? 'locked' : '';
          const icon = m.state==='done' ? ICON.check : m.state==='locked' ? ICON.lock : ICON.play;
          return `
          <div class="module ${cls}" data-mod="${m.id}" data-state="${m.state}">
            <div class="m-icon">${icon}</div>
            <div class="m-body">
              <div class="m-title">${esc(m.title)}</div>
              <div class="m-meta">${esc(m.meta)}</div>
            </div>
            <div class="m-chev">${ICON.chev}</div>
          </div>`;
        }).join('')}
        <button class="btn" data-go="P-10" style="margin-top:4px">Mock-интервью по треку</button>
      </div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelectorAll('[data-mod]').forEach(el=>{
      el.addEventListener('click', ()=>{
        if(el.dataset.state === 'locked') return;
        s.currentModuleId = el.dataset.mod;
        // AI trainer modules go straight to P-4
        const mod = CASE_MODULES.find(m=>m.id===el.dataset.mod);
        if(mod && mod.title.toLowerCase().includes('тренажёр')){
          a.goTo('P-4');
        } else if(mod && mod.title.toLowerCase().includes('mock')){
          a.goTo('P-10');
        } else {
          a.goTo('P-3');
        }
      });
    });
  }
};

/* =====================================================================
   P-3: Модуль (урок)
   ===================================================================== */
const P3 = {
  id:'P-3', name:'Урок',
  render(s){
    const mod = CASE_MODULES.find(m=>m.id===(s.currentModuleId||'c6')) || CASE_MODULES[5];
    return `
    <div class="screen active has-tabbar" data-id="P-3">
      <div class="s-head">
        <button class="back" data-go="P-2">${ICON.back}</button>
        <div class="pill">${esc(mod.meta)}</div>
      </div>
      <div class="screen-scroll">
        <div class="title">${esc(mod.title)}</div>

        <div class="video-stub">
          <div class="play">${ICON.play}</div>
          <div class="dur">08:12</div>
        </div>

        <div style="font-size:14px;line-height:1.6;color:var(--ink)">
          <p style="margin:0 0 10px"><b>Profitability framework</b> — рабочий каркас для вопросов «почему упала прибыль» или «как увеличить её».</p>
          <p style="margin:0 0 10px">Формула проста: <b>Прибыль = Выручка − Затраты</b>. Дальше разбираем каждую ветку отдельно — по продуктам, сегментам клиентов, каналам.</p>
          <p style="margin:0 0 10px">Когда использовать: любой вопрос про финансы компании или отдельного направления. Когда не стоит: если задача явно про рынок или операционную эффективность — там лучше market или ops-фреймворки.</p>
        </div>

        <div class="ai">
          <div class="ai-label">Ключевые вопросы себе</div>
          <p>1. Проблема в выручке или затратах?</p>
          <p>2. Какой сегмент / продукт просел?</p>
          <p>3. Это внутренняя история или внешний рынок?</p>
        </div>

        <div class="btn-row" style="margin-top:8px">
          <button class="btn ghost" data-go="P-2">Назад к треку</button>
          <button class="btn" data-go="P-4">Начать тренировку</button>
        </div>
      </div>
    </div>`;
  }
};

/* =====================================================================
   P-4: AI-тренажёр (инструктаж)
   ===================================================================== */
const P4 = {
  id:'P-4', name:'AI-тренажёр · брифинг',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="P-4">
      <div class="s-head">
        <button class="back" data-go="P-2">${ICON.back}</button>
        <div class="pill">AI-тренажёр</div>
      </div>
      <div class="screen-scroll">
        <div class="question-card">
          <div class="q-label">Задача на market sizing</div>
          Сколько примерно лифтов работает в Москве?
          <div style="font-size:12px;color:var(--ink-2);font-weight:400;margin-top:10px">
            Точная цифра не нужна. Важна структура и разумные допущения.
          </div>
        </div>

        <div style="font-size:13px;color:var(--ink-2);font-weight:500;letter-spacing:.4px;text-transform:uppercase">
          Как пройдёт
        </div>
        <ul class="rules">
          <li>Запиши аудио-ответ до 3 минут</li>
          <li>AI расшифрует речь и оценит структуру</li>
          <li>Получишь фидбэк и рекомендацию, что подтянуть</li>
        </ul>

        <div class="ai">
          <div class="ai-label">Подсказка</div>
          <p>Начни со структуры: «Разобью на два пути — жилые дома и коммерческая недвижимость».</p>
          <p>Думай вслух: AI оценит не только ответ, но и ход рассуждений.</p>
        </div>

        <div class="spacer"></div>
        <button class="btn" data-go="P-5">Начать запись</button>
        <button class="btn ghost" style="margin-top:8px" data-act="skip">Пропустить · следующий вопрос</button>
      </div>
    </div>`;
  }
};

/* =====================================================================
   P-5: Запись ответа
   ===================================================================== */
const P5 = {
  id:'P-5', name:'AI-тренажёр · запись',
  render(s){
    const recording = s.recording !== false; // default true when entering
    return `
    <div class="screen active has-tabbar" data-id="P-5">
      <div class="s-head">
        <button class="back" data-go="P-4">${ICON.back}</button>
        <div class="pill">AI-тренажёр · запись</div>
      </div>
      <div class="question-card" style="font-size:14.5px">
        Сколько примерно лифтов работает в Москве?
      </div>

      <div class="recorder">
        <div class="rec-timer" id="rec-timer">${s.recTimer||'00:00'}</div>
        ${recording ? `
          <div class="wave">
            ${Array.from({length:24}, (_,i)=>`<span style="animation-delay:${(i%6)*0.08}s"></span>`).join('')}
          </div>` : `
          <div style="height:60px;display:flex;align-items:center;color:var(--ink-2);font-size:13px">Запись на паузе</div>`
        }
        <button class="rec-button ${recording?'stop':''}" data-act="toggle"></button>
        <div class="rec-hint">${recording?'Нажми, чтобы остановить':'Нажми, чтобы записать'}</div>
      </div>

      <button class="btn" data-go="P-6" style="margin-top:auto">Закончить и получить разбор</button>
    </div>`;
  },
  bind(root, s, a){
    // start timer if not running
    if(!s._timerI){
      s.recording = s.recording !== false;
      s._timerStart = s._timerStart || Date.now();
      s._timerI = setInterval(()=>{
        if(!s.recording) return;
        const sec = Math.floor((Date.now()-s._timerStart)/1000);
        const mm = String(Math.floor(sec/60)).padStart(2,'0');
        const ss = String(sec%60).padStart(2,'0');
        s.recTimer = `${mm}:${ss}`;
        const el = document.getElementById('rec-timer');
        if(el) el.textContent = s.recTimer;
        if(sec >= 180){ clearInterval(s._timerI); s._timerI=null; a.goTo('P-6'); }
      }, 250);
    }
    root.querySelector('[data-act="toggle"]').addEventListener('click', ()=>{
      s.recording = !s.recording;
      a.rerender();
    });
    // stop timer on navigation away
    const cleanup = ()=>{
      if(s._timerI){ clearInterval(s._timerI); s._timerI=null; }
    };
    window.__prepCleanup = cleanup;
  }
};

/* =====================================================================
   P-6: AI-разбор
   ===================================================================== */
const P6 = {
  id:'P-6', name:'AI-разбор ответа',
  render(s){
    const score = 72;
    const circ = 2 * Math.PI * 52;
    const dash = circ * (1 - score/100);
    return `
    <div class="screen active has-tabbar" data-id="P-6">
      <div class="s-head">
        <button class="back" data-go="P-5">${ICON.back}</button>
        <div class="pill">AI-разбор</div>
      </div>
      <div class="screen-scroll">
        <div class="score-ring">
          <svg viewBox="0 0 120 120">
            <circle class="ring-track" cx="60" cy="60" r="52"/>
            <circle class="ring-val" cx="60" cy="60" r="52"
              stroke-dasharray="${circ}" stroke-dashoffset="${dash}"/>
          </svg>
          <div class="score-num"><b>${score}</b><span>/100</span></div>
        </div>
        <div style="text-align:center;font-size:13px;color:var(--ink-2);margin-top:-4px">
          Хороший ответ для первой попытки
        </div>

        <div class="fb-block">
          <div class="fb-head"><span class="ic good">+</span>Что хорошо</div>
          <ul>
            <li>Структура: разделил на жилые и коммерческие здания — это MECE-подход</li>
            <li>Чётко озвучил допущения про количество этажей и лифтов на здание</li>
            <li>Проверил результат через second opinion (сравнение с Нью-Йорком)</li>
          </ul>
        </div>

        <div class="fb-block">
          <div class="fb-head"><span class="ic bad">!</span>Что улучшить</div>
          <ul>
            <li>Не учёл «особые» типы зданий: ТЦ, больницы, метро</li>
            <li>Допущение про 8 этажей — типичная ошибка, нужно разделить на сегменты</li>
            <li>Долгая пауза перед структурой (≈22 сек) — начинай со слов «разделю на...»</li>
          </ul>
        </div>

        <div class="fb-block">
          <div class="fb-head"><span class="ic tip">→</span>Что сделать дальше</div>
          <ul>
            <li>Пройди модуль «Типы зданий для market sizing»</li>
            <li>Сделай ещё 2 задачи из этой серии — идеально завтра</li>
          </ul>
        </div>

        <button class="btn" data-go="P-4">Следующая задача</button>
        <button class="btn ghost" data-go="P-2">К треку</button>
      </div>
    </div>`;
  }
};

/* =====================================================================
   P-7: Библиотека материалов
   ===================================================================== */
const P7 = {
  id:'P-7', name:'Библиотека',
  render(s){
    const q = (s.libQuery||'').toLowerCase();
    const kind = s.libKind || 'all';
    let items = LIBRARY;
    if(kind !== 'all') items = items.filter(x=>x.kind===kind);
    if(q) items = items.filter(x=>x.title.toLowerCase().includes(q));
    return `
    <div class="screen active has-tabbar" data-id="P-7">
      <div class="screen-header">
        <div class="h-action" data-go="P-1">${ICON.back}</div>
        <div class="h-title" style="flex:1;text-align:center">Библиотека</div>
        <div style="width:34px"></div>
      </div>
      <input class="input" placeholder="Поиск по материалам" id="lib-q" value="${esc(s.libQuery||'')}">
      <div class="chip-scroll" style="margin-top:8px">
        ${['all','article','video','sheet'].map(k=>`<div class="chip ${kind===k?'active':''}" data-kind="${k}">${({all:'Все',article:'Статьи',video:'Видео',sheet:'Шпаргалки'})[k]}</div>`).join('')}
      </div>
      <div class="screen-scroll" style="margin-top:6px">
        ${items.length===0
          ? `<div class="empty"><div class="msg">Ничего не найдено</div></div>`
          : items.map(x=>`
            <div class="lib-item" data-lib="${x.id}">
              <div class="thumb">${ICON[x.kind==='sheet'?'sheet':x.kind==='video'?'video':'article']}</div>
              <div class="lib-body">
                <div class="lib-title">${esc(x.title)}</div>
                <div class="lib-meta">${esc(x.meta)}</div>
              </div>
            </div>`).join('')
        }
      </div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelector('#lib-q').addEventListener('input', e=>{ s.libQuery = e.target.value; a.rerender(); setTimeout(()=>{ const el=document.getElementById('lib-q'); if(el){ el.focus(); el.setSelectionRange(el.value.length,el.value.length); }},0); });
    root.querySelectorAll('[data-kind]').forEach(el=>{
      el.addEventListener('click', ()=>{ s.libKind = el.dataset.kind; a.rerender(); });
    });
    root.querySelectorAll('[data-lib]').forEach(el=>{
      el.addEventListener('click', ()=>{ s.currentLibId = el.dataset.lib; a.goTo('P-8'); });
    });
  }
};

/* =====================================================================
   P-8: Материал (чтение)
   ===================================================================== */
const P8 = {
  id:'P-8', name:'Материал',
  render(s){
    const item = LIBRARY.find(x=>x.id===(s.currentLibId||'l1')) || LIBRARY[0];
    return `
    <div class="screen active has-tabbar" data-id="P-8">
      <div class="s-head">
        <button class="back" data-go="P-7">${ICON.back}</button>
        <div class="pill">${esc(item.meta)}</div>
      </div>
      <div class="screen-scroll">
        <div class="title">${esc(item.title)}</div>

        ${item.kind==='video' ? `
          <div class="video-stub">
            <div class="play">${ICON.play}</div>
            <div class="dur">18:04</div>
          </div>` : ''
        }

        <div style="font-size:14px;line-height:1.65;color:var(--ink)">
          <p style="margin:0 0 12px">«Расскажи о себе» — первый и самый предсказуемый вопрос. Его задают на 90% HR-интервью, и при этом большинство кандидатов проваливают именно его.</p>
          <p style="margin:0 0 12px"><b>Что не работает.</b> Длинное перечисление всех курсов и хобби. HR слушает 20 секунд и переключается. Нужна структура.</p>
          <p style="margin:0 0 12px"><b>Формула из 3 частей.</b></p>
          <p style="margin:0 0 8px">1. Кто ты сейчас (курс, программа, 1 предложение).<br>
          2. Что делаешь помимо учёбы, релевантного роли (проекты, волонтёрство, подработки).<br>
          3. Почему пришёл в эту компанию и чем готов быть полезен.</p>
          <p style="margin:0 0 12px">Итого 60–90 секунд. Не дольше.</p>
        </div>

        <div class="ai">
          <div class="ai-label">Твоё «про себя» — черновик</div>
          <p>AI составит персональную версию на основе твоего профиля и вакансии, когда ты выберешь конкретную компанию.</p>
        </div>

        <button class="btn" data-go="P-4">Тренировать этот ответ</button>
      </div>
    </div>`;
  }
};

/* =====================================================================
   P-9: План на неделю
   ===================================================================== */
const P9 = {
  id:'P-9', name:'План на неделю',
  render(s){
    const tasks = s.planTasks || PLAN_TASKS;
    const done = tasks.filter(t=>t.done).length;
    return `
    <div class="screen active has-tabbar" data-id="P-9">
      <div class="s-head">
        <button class="back" data-go="P-1">${ICON.back}</button>
        <div class="pill">Неделя 15–21 апреля</div>
      </div>
      <div class="title">План на неделю</div>
      <div class="subtitle">${done} из ${tasks.length} задач · AI обновит план в воскресенье</div>
      <div class="screen-scroll" style="margin-top:8px">
        ${tasks.map(t=>`
          <div class="task ${t.done?'done':''}" data-task="${t.id}">
            <div class="t-check">${ICON.check}</div>
            <div class="t-body">
              <div class="t-label">${esc(t.label)}</div>
              <div class="t-meta">${esc(t.meta)}</div>
            </div>
          </div>`).join('')}
        <div class="ai" style="margin-top:4px">
          <div class="ai-label">Почему именно это</div>
          <p>У тебя завтра фоллоу-ап по 2 откликам в консалтинг. За неделю до — самое время прогнать кейс-блок и HR-подготовку.</p>
        </div>
      </div>
    </div>`;
  },
  bind(root, s, a){
    s.planTasks = s.planTasks || PLAN_TASKS.map(t=>({...t}));
    root.querySelectorAll('[data-task]').forEach(el=>{
      el.addEventListener('click', ()=>{
        const t = s.planTasks.find(x=>x.id===el.dataset.task);
        if(t){ t.done = !t.done; a.rerender(); }
      });
    });
  }
};

/* =====================================================================
   P-10: Mock-интервью (вопрос из серии)
   ===================================================================== */
const P10 = {
  id:'P-10', name:'Mock-интервью',
  render(s){
    const idx = s.mockIdx || 0;
    const q = MOCK_QUESTIONS[idx] || MOCK_QUESTIONS[0];
    return `
    <div class="screen active has-tabbar" data-id="P-10">
      <div class="s-head">
        <button class="back" data-go="P-1">${ICON.back}</button>
        <div class="pill">Mock-интервью · ${idx+1}/${MOCK_QUESTIONS.length}</div>
      </div>
      <div class="q-progress">
        ${MOCK_QUESTIONS.map((_,i)=>`<div class="d ${i<idx?'done':i===idx?'active':''}"></div>`).join('')}
      </div>

      <div class="question-card">
        <div class="q-label">Вопрос ${idx+1}</div>
        ${esc(q)}
      </div>

      <div class="recorder" style="padding-top:10px">
        <div class="rec-timer">01:12</div>
        <div class="wave">
          ${Array.from({length:24}, (_,i)=>`<span style="animation-delay:${(i%6)*0.08}s"></span>`).join('')}
        </div>
        <button class="rec-button stop" data-act="next"></button>
        <div class="rec-hint">Нажми, чтобы закончить ответ</div>
      </div>

      <button class="btn ghost" data-act="skip" style="margin-top:auto">Пропустить вопрос</button>
    </div>`;
  },
  bind(root, s, a){
    const advance = ()=>{
      s.mockIdx = (s.mockIdx||0) + 1;
      if(s.mockIdx >= MOCK_QUESTIONS.length){
        s.mockIdx = 0;
        a.goTo('P-10b');
      } else {
        a.rerender();
      }
    };
    root.querySelector('[data-act="next"]').addEventListener('click', advance);
    root.querySelector('[data-act="skip"]').addEventListener('click', advance);
  }
};

/* =====================================================================
   P-10b: Итоговый отчёт mock
   ===================================================================== */
const P10b = {
  id:'P-10b', name:'Mock · отчёт',
  render(s){
    const score = 78;
    const circ = 2 * Math.PI * 52;
    const dash = circ * (1 - score/100);
    return `
    <div class="screen active has-tabbar" data-id="P-10b">
      <div class="s-head">
        <button class="back" data-go="P-10">${ICON.back}</button>
        <div class="pill">Отчёт после mock</div>
      </div>
      <div class="screen-scroll">
        <div class="score-ring">
          <svg viewBox="0 0 120 120">
            <circle class="ring-track" cx="60" cy="60" r="52"/>
            <circle class="ring-val" cx="60" cy="60" r="52" stroke-dasharray="${circ}" stroke-dashoffset="${dash}"/>
          </svg>
          <div class="score-num"><b>${score}</b><span>/100</span></div>
        </div>
        <div style="text-align:center;font-size:13px;color:var(--ink-2)">
          Крепкий mock · готов к реальному HR
        </div>

        <div class="fb-block">
          <div class="fb-head"><span class="ic good">+</span>Сильные моменты</div>
          <ul>
            <li>«Про себя» — чёткая структура из 3 частей</li>
            <li>Уверенная интонация, почти без пауз</li>
            <li>Связка с компанией — конкретная (годовой отчёт, проект X)</li>
          </ul>
        </div>

        <div class="fb-block">
          <div class="fb-head"><span class="ic bad">!</span>Зоны роста</div>
          <ul>
            <li>Конфликтный кейс — не назвал, чему научился</li>
            <li>«Почему компания» — общие слова про «сильный бренд»</li>
          </ul>
        </div>

        <div class="fb-block">
          <div class="fb-head"><span class="ic tip">→</span>Рекомендуемые следующие шаги</div>
          <ul>
            <li>Модуль «STAR-метод» (10 мин)</li>
            <li>Ещё один mock через 2 дня с фокусом на «почему компания»</li>
          </ul>
        </div>

        <button class="btn" data-go="P-1">Вернуться на главную</button>
        <button class="btn ghost" data-go="P-10">Пройти mock ещё раз</button>
      </div>
    </div>`;
  }
};

return [P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P10b];

})();
