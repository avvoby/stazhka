/* ============================================================
   Stazhka Search tab — screens (S-1 ... S-9∑)
   ============================================================ */

window.Screens = (function(){

function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

/* ---------- Icons ---------- */
const ICON = {
  filter:'<svg viewBox="0 0 24 24"><path d="M3 6h18M6 12h12M10 18h4"/></svg>',
  search:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  bell:'<svg viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9Z"/><path d="M10 21a2 2 0 0 0 4 0"/></svg>',
  heart:'<svg viewBox="0 0 24 24"><path d="M12 20s-8-5-8-11a5 5 0 0 1 9-3 5 5 0 0 1 9 3c0 6-8 11-8 11z"/></svg>',
  plus:'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  back:'<svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg>',
  empty:'<svg viewBox="0 0 24 24"><rect x="4" y="5" width="16" height="14" rx="2"/><path d="M4 9h16M9 13h2"/></svg>'
};

/* ---------- Realistic data ---------- */
const VACANCIES = [
  {id:'v1', role:'Стажёр-аналитик', company:'Сбер', loc:'Москва · гибрид', match:92, tier:'g', link:'sberbank.ru/career/intern',
    about:'Поддержка бизнес-анализа в департаменте розничных продуктов. Excel, SQL, презентации. Отклик до 30 апреля.'},
  {id:'v2', role:'Младший консультант', company:'Яков и Партнёры', loc:'Москва · офис', match:87, tier:'g', link:'yakov.partners/careers',
    about:'Работа в проектных командах стратегического консалтинга. От 3 курса, английский B2+.'},
  {id:'v3', role:'Data-стажёр', company:'Авито', loc:'удалёнка', match:74, tier:'y', link:'avito.ru/career',
    about:'Задачи по анализу продуктовых метрик. Python, SQL, опыт с dashboard приветствуется.'},
  {id:'v4', role:'HR-стажёр', company:'Магнит', loc:'Москва · офис', match:68, tier:'gr', link:'magnit.ru/career',
    about:'Support команды рекрутмента массовых позиций.'},
  {id:'v5', role:'Стажёр в стратегию', company:'Т-Банк', loc:'Москва · гибрид', match:81, tier:'y', link:'tbank.ru/career',
    about:'Аналитика конкурентов и трендов для C-level. Сильный Excel и storytelling.'}
];

/* =====================================================================
   S-1 / S-3 / S-4 / S-5 / S-6 — unified main search screen with tabs
   ===================================================================== */
const S1 = {
  id:'S-1', name:'Поиск · главная',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-1">
      <div class="screen-header">
        <div class="h-title">Поиск</div>
        <div class="h-action" title="Фильтры">${ICON.filter}</div>
      </div>
      <div class="segment">
        <button data-seg="picks" class="${s.searchSeg==='picks'?'active':''}">Подборка</button>
        <button data-seg="manual" class="${s.searchSeg==='manual'?'active':''}">Поиск</button>
        <button data-seg="fav" class="${s.searchSeg==='fav'?'active':''}">Избранное</button>
        <button data-seg="alerts" class="${s.searchSeg==='alerts'?'active':''}">Алерты</button>
      </div>
      <div class="screen-scroll" id="s1-body"></div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelectorAll('[data-seg]').forEach(b=>{
      b.addEventListener('click', ()=>{ s.searchSeg = b.dataset.seg; a.rerender(); });
    });
    renderSegBody(root.querySelector('#s1-body'), s, a);
  }
};

function renderSegBody(host, s, a){
  const seg = s.searchSeg || 'picks';
  if(seg==='picks') return renderPicks(host, s, a);
  if(seg==='manual') return renderManual(host, s, a);
  if(seg==='fav') return renderFav(host, s, a);
  if(seg==='alerts') return renderAlerts(host, s, a);
}

function renderPicks(host, s, a){
  if(window.__TWEAKS.emptyPicks){
    host.innerHTML = `
      <div class="empty">
        <div class="glyph">${ICON.search}</div>
        <div class="msg">Заполни расширенный профиль, чтобы получить подборку</div>
        <button class="btn" style="max-width:240px" id="p-extend">Заполнить</button>
      </div>`;
    host.querySelector('#p-extend').addEventListener('click', ()=> a.goTo('S-2'));
    return;
  }
  host.innerHTML = `
    <div style="font-size:11.5px;color:var(--ink-2);letter-spacing:.3px">
      5 вакансий · обновлено минуту назад
    </div>
    ${VACANCIES.map(v=>vacancyCard(v, s)).join('')}
  `;
  wireVacancyActions(host, s, a);
}

function renderManual(host, s, a){
  const PRESETS = ['Big-3','Big-4','Со 2 курса','От 60к','Программы стажировок'];
  s.manualPreset = s.manualPreset || 'Big-3';
  host.innerHTML = `
    <input class="input" placeholder="Должность, компания или город" value="${esc(s.manualQuery||'')}" id="mq">
    <div class="chip-scroll">
      ${PRESETS.map(p=>`<div class="chip ${s.manualPreset===p?'active':''}" data-preset="${p}">${p}</div>`).join('')}
    </div>
    ${VACANCIES.slice(0,3).map(v=>vacancyCard(v, s)).join('')}
  `;
  host.querySelector('#mq').addEventListener('input', e=>{ s.manualQuery = e.target.value; });
  host.querySelectorAll('[data-preset]').forEach(el=>{
    el.addEventListener('click', ()=>{ s.manualPreset = el.dataset.preset; a.rerender(); });
  });
  wireVacancyActions(host, s, a);
}

function renderFav(host, s, a){
  const favs = VACANCIES.filter(v => s.favorites.includes(v.id));
  if(favs.length === 0){
    host.innerHTML = `
      <div class="empty">
        <div class="glyph">${ICON.heart}</div>
        <div class="msg">Пока пусто. Сохраняй вакансии из подборки</div>
      </div>`;
    return;
  }
  host.innerHTML = favs.map(v=>vacancyCard(v, s, {showRemove:true})).join('');
  wireVacancyActions(host, s, a);
}

function renderAlerts(host, s, a){
  const alerts = s.alerts || [];
  host.innerHTML = `
    <div style="font-size:12.5px;color:var(--ink-2);line-height:1.5;margin-bottom:2px">
      Пришлём уведомление, когда компания откроет стажировку
    </div>
    ${alerts.length===0
      ? `<div class="empty" style="padding:20px 0"><div class="msg">Пока без алертов</div></div>`
      : alerts.map(c=>`
        <div class="tag-row">
          <span>${esc(c)}</span>
          <span class="x" data-rm="${esc(c)}">×</span>
        </div>`).join('')
    }
    <div style="display:flex;gap:8px;margin-top:6px">
      <input class="input" id="alert-in" placeholder="Название компании" style="flex:1">
      <button class="btn" id="alert-add" style="width:auto;padding:0 18px;flex-shrink:0">Добавить</button>
    </div>
    <div style="font-size:11.5px;color:var(--ink-2)">
      ${alerts.length}/10 компаний
    </div>
  `;
  host.querySelectorAll('[data-rm]').forEach(el=>{
    el.addEventListener('click', ()=>{
      s.alerts = s.alerts.filter(x=>x !== el.dataset.rm);
      a.rerender();
    });
  });
  const inp = host.querySelector('#alert-in');
  host.querySelector('#alert-add').addEventListener('click', ()=>{
    const v = inp.value.trim();
    if(v && !s.alerts.includes(v) && s.alerts.length<10){
      s.alerts.push(v);
      a.rerender();
    }
  });
}

/* ---------- Vacancy card ---------- */
function vacancyCard(v, s, opts={}){
  const fav = s.favorites.includes(v.id);
  const hidden = s.hidden.includes(v.id);
  if(hidden) return '';
  return `
    <div class="vacancy" data-vid="${v.id}">
      <div class="top">
        <div class="role">${esc(v.role)}</div>
        <div class="match"><span class="dot ${v.tier}"></span>${v.match}%</div>
      </div>
      <div class="meta">${esc(v.company)} · ${esc(v.loc)}</div>
      <div class="link">${esc(v.link)}</div>
      <div class="actions">
        ${opts.showRemove
          ? `<button class="mini ghost" data-act-v="unfav">Удалить</button>
             <button class="mini primary" data-act-v="apply">Откликнуться</button>`
          : `<button class="mini ghost" data-act-v="fav">${fav?'В избранном':'В избранное'}</button>
             <button class="mini primary" data-act-v="apply">Откликнуться</button>
             <button class="mini ghost" data-act-v="hide">Скрыть</button>`
        }
      </div>
    </div>`;
}

function wireVacancyActions(host, s, a){
  host.querySelectorAll('.vacancy').forEach(card=>{
    const vid = card.dataset.vid;
    card.querySelectorAll('[data-act-v]').forEach(btn=>{
      btn.addEventListener('click', (e)=>{
        e.stopPropagation();
        const act = btn.dataset.actV;
        if(act==='fav'){
          if(!s.favorites.includes(vid)) s.favorites.push(vid);
          else s.favorites = s.favorites.filter(x=>x!==vid);
          a.rerender();
        } else if(act==='unfav'){
          s.favorites = s.favorites.filter(x=>x!==vid);
          a.rerender();
        } else if(act==='hide'){
          s.hidden.push(vid);
          a.rerender();
        } else if(act==='apply'){
          s.applyingVid = vid;
          a.openSheet('apply');
        }
      });
    });
  });
}

/* =====================================================================
   S-2: Extended onboarding intro + 7-step flow compacted
   ===================================================================== */
const S2 = {
  id:'S-2', name:'Расшир. онбординг',
  render(s){
    return `
    <div class="screen active" data-id="S-2">
      <div class="s-head">
        <button class="back" data-act="back">${ICON.back}</button>
        <div class="pill">Первый вход · Подборка</div>
      </div>
      <div class="title">Персонализация подборки</div>
      <div class="subtitle">Ответь на несколько вопросов — это займёт 5-10 минут, зато каждая вакансия будет подобрана под тебя</div>
      <div class="ai" style="margin-top:8px">
        <div class="ai-label">Что настраиваем</div>
        <p>Формат работы, город и релокация, языки, hard skills, размер компании и зарплатные ожидания.</p>
      </div>
      <div class="spacer"></div>
      <button class="btn" data-go="S-2b">Заполнить</button>
      <button class="btn ghost" style="margin-top:8px" data-go="S-1">Позже</button>
    </div>`;
  }
};

/* One representative step of extended onboarding (S-2b): hard skills */
const S2b = {
  id:'S-2b', name:'Расш. онб. · навыки',
  render(s){
    const skills = ['Excel','Python','SQL','PowerPoint','Финмодели','1С','R','Tableau'];
    s.hardSkills = s.hardSkills || [];
    return `
    <div class="screen active" data-id="S-2b">
      <div class="progress"><span style="width:72%"></span></div>
      <div class="s-head">
        <button class="back" data-go="S-2">${ICON.back}</button>
        <div class="pill">Шаг 5 из 7 · Hard skills</div>
      </div>
      <div class="title">Какими навыками владеешь?</div>
      <div class="subtitle">Отметь, что уверенно используешь — для подбора учтём</div>
      <div class="chip-grid">
        ${skills.map(x=>`<div class="chip ${s.hardSkills.includes(x)?'active':''}" data-skill="${x}">${x}</div>`).join('')}
      </div>
      <input class="input" placeholder="Другие навыки через запятую" style="margin-top:10px" id="extra-skills" value="${esc(s.extraSkills||'')}">
      <div class="spacer"></div>
      <div class="btn-row">
        <button class="btn ghost" data-go="S-2">Назад</button>
        <button class="btn" data-go="S-1">Далее</button>
      </div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelectorAll('[data-skill]').forEach(el=>{
      el.addEventListener('click', ()=>{
        const x = el.dataset.skill;
        if(s.hardSkills.includes(x)) s.hardSkills = s.hardSkills.filter(y=>y!==x);
        else s.hardSkills.push(x);
        a.rerender();
      });
    });
    root.querySelector('#extra-skills').addEventListener('input', e=>{ s.extraSkills = e.target.value; });
  }
};

/* =====================================================================
   S-7 as standalone navigable screen (the sheet is opened from S-1 too)
   ===================================================================== */
const S7 = {
  id:'S-7', name:'Отклик · sheet',
  render(s){
    const v = VACANCIES.find(x=>x.id===(s.applyingVid||'v1')) || VACANCIES[0];
    const phase = s.applyPhase || 'letter';
    return `
    <div class="screen active has-tabbar" data-id="S-7">
      <div class="screen-header">
        <div class="h-title">Поиск</div>
      </div>
      <div class="screen-scroll" style="opacity:.45;pointer-events:none">
        ${VACANCIES.slice(0,3).map(x=>vacancyCard(x, s)).join('')}
      </div>
      ${renderApplySheet(v, s, phase)}
    </div>`;
  },
  bind(root, s, a){
    wireApplySheet(root, s, a);
  }
};

function renderApplySheet(v, s, phase){
  if(phase==='loading'){
    return `
      <div class="sheet-backdrop"></div>
      <div class="sheet" style="height:60%">
        <div class="sheet-handle"></div>
        <div class="sheet-title">Отклик на<br>«${esc(v.role)} · ${esc(v.company)}»</div>
        <div class="loader"><span class="spinner"></span>Пишу cover letter под вакансию...</div>
        <div style="font-size:12px;color:var(--ink-2);line-height:1.5">
          Учитываю твой профиль, описание вакансии и опыт из резюме. Обычно 10–15 секунд.
        </div>
        <div class="spacer"></div>
        <button class="btn" aria-disabled="true">Скопировать текст</button>
      </div>`;
  }
  if(phase==='sent'){
    return `
      <div class="sheet-backdrop"></div>
      <div class="sheet" style="height:42%">
        <div class="sheet-handle"></div>
        <div class="sheet-title">Текст скопирован</div>
        <div class="confirm">Добавлено в трекер<br>Статус: Подано</div>
        <div class="spacer"></div>
        <button class="btn ghost" data-act-a="close">Готово</button>
        <button class="btn outline" data-act-a="openLink">Открыть вакансию</button>
      </div>`;
  }
  // letter
  const tone = s.letterTone || 'formal';
  const letterFormal = `
    <p>Здравствуйте! Меня зовут Иван Иванов, я на 3 курсе Бизнес-информатики в ВШБ НИУ ВШЭ. Увидел вакансию стажёра-аналитика в розничных продуктах — хочу попробовать свои силы.</p>
    <p>За два года учёбы собрал практику в Excel и SQL: делал сквозную аналитику по учебному проекту «Пятёрочка», строил модели оттока клиентов. Прошёл курс по кейс-интервью — понимаю MECE и умею декомпозировать задачи.</p>
    <p>Именно ${esc(v.company)} привлёк масштабом данных: хочется работать с реальными миллионами клиентов, а не учебными. Готов к гибриду в Москве и старту в ближайший месяц.</p>
    <p>С уважением,<br>Иван Иванов</p>`;
  const letterCasual = `
    <p>Привет! Я Иван, учусь на 3 курсе Бизнес-информатики в ВШБ. Увидел у вас стажировку аналитиком и хочу откликнуться.</p>
    <p>Последний год активно кручу Excel и SQL — в учебных проектах сам собирал метрики и строил простую модель оттока. Про кейсы и MECE понимаю, недавно прошёл курс.</p>
    <p>Именно ${esc(v.company)} интересен тем, что данных реально много — хочется наконец поработать не с учебной выборкой, а с настоящими клиентами. Готов к гибриду и могу начать скоро.</p>
    <p>Иван</p>`;
  return `
    <div class="sheet-backdrop"></div>
    <div class="sheet" style="height:84%">
      <div class="sheet-handle"></div>
      <div class="sheet-title">Отклик на<br>«${esc(v.role)} · ${esc(v.company)}»</div>
      <div class="sheet-scroll">
        <div class="ai">
          <div class="ai-label">AI cover letter · черновик</div>
          ${tone==='casual'?letterCasual:letterFormal}
        </div>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <div class="chip ${tone==='casual'?'active':''}" data-act-a="toneCasual">Менее формально</div>
        <div class="chip" data-act-a="addExample">Добавить пример</div>
        <div class="chip" data-act-a="regen">Перегенерировать</div>
      </div>
      <button class="btn" data-act-a="copy">Скопировать текст</button>
      <button class="btn ghost" data-act-a="openLink">Открыть вакансию</button>
    </div>`;
}

function wireApplySheet(root, s, a){
  root.querySelectorAll('[data-act-a]').forEach(el=>{
    el.addEventListener('click', ()=>{
      const x = el.dataset.actA;
      if(x==='close'){ s.applyPhase = null; s.applyingVid = null; a.goTo('S-1'); }
      else if(x==='copy'){ s.applyPhase = 'sent'; a.rerender(); }
      else if(x==='toneCasual'){ s.letterTone = s.letterTone==='casual'?'formal':'casual'; a.rerender(); }
      else if(x==='regen'){ s.applyPhase = 'loading'; a.rerender(); setTimeout(()=>{ if(s.applyPhase==='loading'){ s.applyPhase='letter'; a.rerender(); } }, 1400); }
      else if(x==='addExample'){ /* noop prototype */ }
      else if(x==='openLink'){ /* external */ }
    });
  });
}

/* =====================================================================
   S-8 Follow-up (push → screen)
   ===================================================================== */
const S8 = {
  id:'S-8', name:'Фоллоу-ап',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-8">
      <div class="s-head">
        <button class="back" data-go="S-1">${ICON.back}</button>
        <div class="pill">Через 7 дней после отклика</div>
      </div>
      <div class="title">Как дела с откликом в Сбер?</div>
      <div class="subtitle">Ответ поможет обновить трекер и подсказать следующий шаг</div>
      <div class="vacancy" style="margin-top:4px">
        <div class="role">Стажёр-аналитик</div>
        <div class="meta">Сбер · Москва · гибрид</div>
        <div style="font-size:12px;color:var(--ink-2);margin-top:4px">Подано 11 апреля · 7 дней назад</div>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px;margin-top:12px">
        <button class="fu-btn primary" data-go="S-8-next">Позвали дальше <span class="arrow">→</span></button>
        <button class="fu-btn" data-go="S-8-wait">Жду ответа <span class="arrow">→</span></button>
        <button class="fu-btn danger" data-go="S-9a">Отказали <span class="arrow">→</span></button>
      </div>
      <div class="spacer"></div>
      <div style="text-align:center;font-size:11.5px;color:var(--ink-2)">Открыто из push-уведомления</div>
    </div>`;
  }
};

const S8next = {
  id:'S-8-next', name:'Позвали дальше',
  render(s){
    const stages = ['Тестовое','HR-скрининг','Кейс','Финальное'];
    s.inviteStage = s.inviteStage || null;
    return `
    <div class="screen active has-tabbar" data-id="S-8-next">
      <div class="s-head">
        <button class="back" data-go="S-8">${ICON.back}</button>
        <div class="pill">Сбер · Стажёр-аналитик</div>
      </div>
      <div class="title">На какой этап пригласили?</div>
      <div class="subtitle">Откроем подготовку именно под этот этап</div>
      <div class="rowlist">
        ${stages.map(x=>`<div class="radio-row ${s.inviteStage===x?'active':''}" data-stage="${x}">
          <span class="dot-r"></span><span>${x}</span>
        </div>`).join('')}
      </div>
      <div class="spacer"></div>
      <button class="btn" ${s.inviteStage?'':'aria-disabled="true"'} data-go="S-1">Открыть подготовку</button>
    </div>`;
  },
  bind(root, s, a){
    root.querySelectorAll('[data-stage]').forEach(el=>{
      el.addEventListener('click', ()=>{ s.inviteStage = el.dataset.stage; a.rerender(); });
    });
  }
};

const S8wait = {
  id:'S-8-wait', name:'Жду ответа',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-8-wait">
      <div class="s-head">
        <button class="back" data-go="S-8">${ICON.back}</button>
        <div class="pill">Сбер · Стажёр-аналитик</div>
      </div>
      <div class="title">Написать работодателю</div>
      <div class="subtitle">Тон уважительный — это первое письмо после паузы</div>
      <div class="ai">
        <div class="ai-label">AI-текст для отправки</div>
        <p>Добрый день! Неделю назад откликнулся на вакансию стажёра-аналитика. Подскажите, пожалуйста, рассматривается ли моё резюме и нужна ли от меня дополнительная информация?</p>
        <p>Буду благодарен за любой ответ о статусе.</p>
        <p>С уважением,<br>Иван Иванов</p>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap">
        <div class="chip">Короче</div>
        <div class="chip">Менее формально</div>
      </div>
      <div class="spacer"></div>
      <button class="btn" data-act="copy">Скопировать текст</button>
      <button class="btn ghost" style="margin-top:8px" data-go="S-1">Напомнить через 3 дня</button>
    </div>`;
  }
};

/* =====================================================================
   S-9 Rejects diary (a-d) + pattern
   ===================================================================== */
const STAGES_REJECT = ['Скрининг','Тестовое','HR-скрининг','Кейс','Финальное'];

const S9a = {
  id:'S-9a', name:'Отказ · этап',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-9a">
      <div class="s-head">
        <button class="back" data-go="S-8">${ICON.back}</button>
        <div class="pill">Дневник отказов · 1/4</div>
      </div>
      <div class="title">На каком этапе отсеяли?</div>
      <div class="subtitle">Сбер · Стажёр-аналитик</div>
      <div class="rowlist">
        ${STAGES_REJECT.map(x=>`<div class="radio-row ${s.rejectStage===x?'active':''}" data-stage="${x}">
          <span class="dot-r"></span><span>${x}</span>
        </div>`).join('')}
      </div>
      <div class="spacer"></div>
      <button class="btn" ${s.rejectStage?'':'aria-disabled="true"'} data-go="S-9b">Далее</button>
    </div>`;
  },
  bind(root, s, a){
    root.querySelectorAll('[data-stage]').forEach(el=>{
      el.addEventListener('click', ()=>{ s.rejectStage = el.dataset.stage; a.rerender(); });
    });
  }
};

const S9b = {
  id:'S-9b', name:'Отказ · фидбэк',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-9b">
      <div class="s-head">
        <button class="back" data-go="S-9a">${ICON.back}</button>
        <div class="pill">Дневник отказов · 2/4</div>
      </div>
      <div class="title">Дали фидбэк?</div>
      <div class="subtitle">Запиши дословно или своими словами — пригодится для AI-анализа</div>
      <textarea class="textarea" placeholder="Например: «На HR-этапе ответы были слишком общими»" id="fb">${esc(s.rejectFeedback||'')}</textarea>
      <button class="btn ghost" data-act="noFb" style="margin-top:8px">Нет фидбэка</button>
      <div class="spacer"></div>
      <div class="btn-row">
        <button class="btn ghost" data-go="S-9a">Назад</button>
        <button class="btn" data-go="S-9c">Далее</button>
      </div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelector('#fb').addEventListener('input', e=>{ s.rejectFeedback = e.target.value; });
    root.querySelector('[data-act="noFb"]').addEventListener('click', ()=>{
      s.rejectFeedback = 'Без фидбэка';
      a.goTo('S-9c');
    });
  }
};

const S9c = {
  id:'S-9c', name:'Отказ · причина',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-9c">
      <div class="s-head">
        <button class="back" data-go="S-9b">${ICON.back}</button>
        <div class="pill">Дневник отказов · 3/4</div>
      </div>
      <div class="title">Что сам считаешь причиной?</div>
      <div class="subtitle">Честный ответ — только для тебя и AI-анализа</div>
      <textarea class="textarea" placeholder="Например: плохо подготовился к вопросу «почему эта компания»" id="rs">${esc(s.rejectReason||'')}</textarea>
      <div class="spacer"></div>
      <div class="btn-row">
        <button class="btn ghost" data-go="S-9b">Назад</button>
        <button class="btn" data-go="S-9d">Далее</button>
      </div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelector('#rs').addEventListener('input', e=>{ s.rejectReason = e.target.value; });
  }
};

const S9d = {
  id:'S-9d', name:'Отказ · что иначе',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-9d">
      <div class="s-head">
        <button class="back" data-go="S-9c">${ICON.back}</button>
        <div class="pill">Дневник отказов · 4/4</div>
      </div>
      <div class="title">Что сделаешь иначе?</div>
      <div class="subtitle">Одно конкретное действие на следующий раз</div>
      <textarea class="textarea" placeholder="Например: пройду 3 mock HR-интервью" id="rd">${esc(s.rejectDiff||'')}</textarea>
      <div class="spacer"></div>
      <button class="btn" data-go="S-9e">Записать</button>
      <div style="text-align:center;font-size:11.5px;color:var(--ink-2);margin-top:8px">+5 очков за разбор отказа</div>
    </div>`;
  },
  bind(root, s, a){
    root.querySelector('#rd').addEventListener('input', e=>{ s.rejectDiff = e.target.value; });
  }
};

const S9e = {
  id:'S-9e', name:'Отказ · записано',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-9e">
      <div class="s-head">
        <button class="back" data-go="S-9d">${ICON.back}</button>
        <div class="pill">Готово</div>
      </div>
      <div class="title">Записано</div>
      <div class="subtitle">Найдёшь разбор в «Прогресс → Мои отклики»</div>
      <div class="confirm" style="margin-top:6px">
        ${esc(s.rejectStage||'—')} · Сбер<br>
        <span style="font-weight:400;font-size:13px;opacity:.8">Причина и план записаны</span>
      </div>
      <div class="spacer"></div>
      <button class="btn" data-go="S-1">К подборке</button>
      <button class="btn ghost" style="margin-top:8px" data-go="S-9pattern">Посмотреть паттерн (5+ отказов)</button>
    </div>`;
  }
};

const S9pattern = {
  id:'S-9pattern', name:'Паттерн отказов',
  render(s){
    return `
    <div class="screen active has-tabbar" data-id="S-9pattern">
      <div class="s-head">
        <button class="back" data-go="S-9e">${ICON.back}</button>
        <div class="pill">После 5+ отказов</div>
      </div>
      <div class="title">Заметил паттерн</div>
      <div class="screen-scroll" style="margin-top:4px">
        <div class="pattern-card">
          <div class="head">5 отказов · 3 на HR-этапе</div>
          <div style="font-size:13px;color:var(--ink);line-height:1.5">
            В 3 из 5 случаев отсев на HR-скрининге. Общее место: вопрос «почему именно эта компания».
          </div>
        </div>
        <div class="ai">
          <div class="ai-label">Что подтянуть</div>
          <p><b>1. Глубинное знание компании.</b> Читай годовой отчёт, новости и отзывы сотрудников за 2 недели до интервью.</p>
          <p><b>2. Структура ответа.</b> 3 пункта: что в компании, что в отделе, что в тебе. Репетируй вслух.</p>
          <p><b>3. Mock HR-сессии.</b> У тебя 0 тренировок — запланируй минимум 3 до следующего скрининга.</p>
        </div>
        <button class="btn">Перейти в Подготовку</button>
        <button class="btn ghost">Скрыть на неделю</button>
      </div>
    </div>`;
  }
};

return [S1, S2, S2b, S7, S8, S8next, S8wait, S9a, S9b, S9c, S9d, S9e, S9pattern];

})();
