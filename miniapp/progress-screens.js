/* Progress tab — G-1..G-5 */
window.Screens = (function(){
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

const ICON={
  back:'<svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg>',
  check:'<svg viewBox="0 0 24 24"><path d="M5 12l4 4L19 7"/></svg>',
  x:'<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  clock:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  chart:'<svg viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/></svg>',
  trophy:'<svg viewBox="0 0 24 24"><path d="M8 4h8v6a4 4 0 0 1-8 0V4zM4 4h4v4a2 2 0 0 1-4 0V4zM16 4h4v4a2 2 0 0 1-4 0V4zM10 14v4H8v2h8v-2h-2v-4"/></svg>',
};

const APPS=[
  {id:'a1',role:'Стажёр-аналитик',company:'Сбер',date:'11 апр',status:'hr',statusLabel:'HR-скрининг',stage:2},
  {id:'a2',role:'Младший консультант',company:'Яков и Партнёры',date:'9 апр',status:'case',statusLabel:'Кейс',stage:3},
  {id:'a3',role:'Data-стажёр',company:'Авито',date:'7 апр',status:'rejected',statusLabel:'Отказ',stage:1,rejectStage:'HR-скрининг'},
  {id:'a4',role:'Стажёр в стратегию',company:'Т-Банк',date:'5 апр',status:'submitted',statusLabel:'Подано',stage:0},
  {id:'a5',role:'HR-стажёр',company:'Магнит',date:'2 апр',status:'offer',statusLabel:'Оффер',stage:5},
  {id:'a6',role:'BI-стажёр',company:'X5 Group',date:'29 мар',status:'rejected',statusLabel:'Отказ',stage:3,rejectStage:'Кейс'},
  {id:'a7',role:'Стратег. стажёр',company:'Kept',date:'25 мар',status:'rejected',statusLabel:'Отказ',stage:1,rejectStage:'HR-скрининг'},
];

const STAGES=[
  {key:'submitted',label:'Подано',icon:'check'},
  {key:'screening',label:'Скрининг резюме',icon:'check'},
  {key:'hr',label:'HR-интервью',icon:'check'},
  {key:'case',label:'Кейс-интервью',icon:'check'},
  {key:'final',label:'Финальное',icon:'check'},
  {key:'offer',label:'Оффер',icon:'check'},
];

/* G-1 */
const G1={id:'G-1',name:'Прогресс · главная',render(s){
  const active = APPS.filter(a=>!['rejected','offer'].includes(a.status)).length;
  const interviews = APPS.filter(a=>['hr','case','final'].includes(a.status)).length;
  const offers = APPS.filter(a=>a.status==='offer').length;
  return `
  <div class="screen active has-tabbar" data-id="G-1">
    <div class="screen-header">
      <div class="h-title">Прогресс</div>
      <div class="h-action" data-go="G-4">${ICON.chart}</div>
    </div>
    <div class="screen-scroll">
      <div class="stats-row">
        <div class="stat"><div class="s-num">${APPS.length}</div><div class="s-label">Откликов</div></div>
        <div class="stat"><div class="s-num">${interviews}</div><div class="s-label">Интервью</div></div>
        <div class="stat"><div class="s-num">${offers}</div><div class="s-label">Оффер</div></div>
      </div>

      <div class="streak">
        <div class="s-icon">🔥</div>
        <div style="flex:1">
          <div class="s-big">12 дней подряд</div>
          <div class="s-sub">Активность в подготовке · не прерывай</div>
        </div>
      </div>

      <div class="level-card">
        <div class="l-top"><span class="l-name">Уровень 4 · Стратег</span><span class="l-next">+320 до 5 уровня</span></div>
        <div class="bar"><span style="width:56%"></span></div>
        <div style="font-size:11.5px;color:var(--ink-2)">840 / 1160 очков</div>
      </div>

      <div class="sec-head">
        <div class="s-title">Активные отклики</div>
        <div class="s-more" data-go="G-2">Все ${APPS.length}</div>
      </div>
      ${APPS.filter(a=>!['rejected','offer'].includes(a.status)).slice(0,3).map(appCard).join('')}

      <div class="sec-head">
        <div class="s-title">Достижения</div>
        <div class="s-more" data-go="G-5">Все</div>
      </div>
      <div class="badges">
        ${[['🎯','Первый отклик','earned'],['🔥','7 дней подряд','earned'],['🧩','5 кейсов','earned'],['⭐','Mock 80+','locked'],['💼','Первый оффер','locked'],['📚','10 модулей','locked']].map(([ic,n,st])=>`
          <div class="badge ${st}"><div class="b-ic">${ic}</div><div class="b-name">${n}</div></div>
        `).join('')}
      </div>
    </div>
  </div>`;
},bind(r,s,a){r.querySelectorAll('[data-app]').forEach(el=>el.addEventListener('click',()=>{s.currentAppId=el.dataset.app;a.goTo('G-3')}))}};

function appCard(a){
  const pillCls = {submitted:'submitted',hr:'hr',case:'case',offer:'offer',rejected:'rejected',screening:'submitted',final:'case'}[a.status]||'submitted';
  return `<div class="app-card" data-app="${a.id}">
    <div class="a-top">
      <div>
        <div class="a-role">${esc(a.role)}</div>
        <div class="a-company">${esc(a.company)}</div>
      </div>
      <span class="status-pill ${pillCls}">${esc(a.statusLabel)}</span>
    </div>
    <div class="a-date">Подано ${esc(a.date)}</div>
  </div>`;
}

/* G-2 */
const G2={id:'G-2',name:'Мои отклики',render(s){
  s.appFilter = s.appFilter || 'all';
  const counts = {
    all: APPS.length,
    active: APPS.filter(a=>!['rejected','offer'].includes(a.status)).length,
    rejected: APPS.filter(a=>a.status==='rejected').length,
    offer: APPS.filter(a=>a.status==='offer').length,
  };
  let list = APPS;
  if(s.appFilter==='active') list = APPS.filter(a=>!['rejected','offer'].includes(a.status));
  else if(s.appFilter==='rejected') list = APPS.filter(a=>a.status==='rejected');
  else if(s.appFilter==='offer') list = APPS.filter(a=>a.status==='offer');
  return `
  <div class="screen active has-tabbar" data-id="G-2">
    <div class="s-head">
      <button class="back" data-go="G-1">${ICON.back}</button>
      <div class="pill">Мои отклики</div>
    </div>
    <div class="chip-scroll" style="margin-top:4px">
      ${[['all','Все'],['active','Активные'],['rejected','Отказы'],['offer','Офферы']].map(([k,l])=>`
        <div class="chip count-badge ${s.appFilter===k?'active':''}" data-filter="${k}">${l}<span class="cb-count">${counts[k]}</span></div>
      `).join('')}
    </div>
    <div class="screen-scroll" style="margin-top:6px">
      ${list.length===0 ? `<div class="empty"><div class="msg">Пусто в этой категории</div></div>` : list.map(appCard).join('')}
    </div>
  </div>`;
},bind(r,s,a){
  r.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',()=>{s.appFilter=el.dataset.filter;a.rerender()}));
  r.querySelectorAll('[data-app]').forEach(el=>el.addEventListener('click',()=>{s.currentAppId=el.dataset.app;a.goTo('G-3')}));
}};

/* G-3 */
const G3={id:'G-3',name:'Карточка отклика',render(s){
  const app = APPS.find(x=>x.id===(s.currentAppId||'a1')) || APPS[0];
  const stages = ['Подано','Скрининг резюме','HR-интервью','Кейс-интервью','Финальное','Оффер'];
  const isRejected = app.status==='rejected';
  const currentIdx = app.stage;
  return `
  <div class="screen active has-tabbar" data-id="G-3">
    <div class="s-head">
      <button class="back" data-go="G-2">${ICON.back}</button>
      <div class="pill">${esc(app.statusLabel)}</div>
    </div>
    <div class="title">${esc(app.role)}</div>
    <div class="subtitle">${esc(app.company)} · подано ${esc(app.date)}</div>
    <div class="screen-scroll" style="margin-top:10px">
      <div class="timeline">
        ${stages.map((st,i)=>{
          let cls='';
          if(isRejected){
            if(i < currentIdx) cls='done';
            else if(i === currentIdx) cls='rejected';
          } else {
            if(i < currentIdx) cls='done';
            else if(i === currentIdx) cls='current';
          }
          const icon = cls==='done'?ICON.check : cls==='rejected'?ICON.x : cls==='current'?'<span style="width:8px;height:8px;background:var(--accent);border-radius:50%"></span>':'';
          return `
          <div class="tl-item ${cls}">
            <div class="tl-dot">${icon}</div>
            <div class="tl-body">
              <div class="tl-title">${st}</div>
              <div class="tl-meta">${i<currentIdx?'пройдено':i===currentIdx?(isRejected?'отсеяли здесь':'сейчас'):'впереди'}</div>
              ${i===currentIdx && isRejected ? `<div class="tl-note">Фидбэк: «Ответы были слишком общими». Разбор в Дневнике отказов.</div>` : ''}
              ${i===currentIdx && !isRejected ? `<div class="tl-note">Рекомендация AI: повтори модуль «${st}» в Подготовке и сделай 1 mock.</div>` : ''}
            </div>
          </div>`;
        }).join('')}
      </div>

      ${isRejected ? `
        <a class="btn" href="Stazhka Search.html#S-9a">К разбору отказа</a>
      ` : app.status==='offer' ? `
        <div class="confirm">🎉 Оффер получен</div>
        <button class="btn">Записать решение</button>
      ` : `
        <a class="btn" href="Stazhka Prep.html#P-2">Открыть подготовку к этапу</a>
        <a class="btn ghost" href="Stazhka Search.html#S-8-wait">Написать работодателю</a>
      `}
    </div>
  </div>`;
}};

/* G-4 */
const G4={id:'G-4',name:'Статистика',render(s){
  const weeks = [
    {l:'12 фев',sub:1,int:0,rej:0,off:0},
    {l:'19 фев',sub:2,int:1,rej:0,off:0},
    {l:'26 фев',sub:1,int:1,rej:1,off:0},
    {l:'4 мар',sub:2,int:2,rej:0,off:0},
    {l:'11 мар',sub:3,int:2,rej:1,off:0},
    {l:'18 мар',sub:1,int:1,rej:1,off:0},
    {l:'25 мар',sub:2,int:2,rej:1,off:0},
    {l:'1 апр',sub:3,int:3,rej:0,off:1},
  ];
  const maxTotal = Math.max(...weeks.map(w=>w.sub+w.int+w.rej+w.off));
  const funnel = [
    {l:'Подано',n:12,pct:100,cls:''},
    {l:'Скрининг',n:9,pct:75,cls:''},
    {l:'HR',n:5,pct:42,cls:''},
    {l:'Кейс',n:3,pct:25,cls:''},
    {l:'Финал',n:2,pct:17,cls:''},
    {l:'Оффер',n:1,pct:8,cls:'dim'},
  ];
  return `
  <div class="screen active has-tabbar" data-id="G-4">
    <div class="s-head">
      <button class="back" data-go="G-1">${ICON.back}</button>
      <div class="pill">Последние 8 недель</div>
    </div>
    <div class="screen-scroll">
      <div class="title" style="font-size:22px">Статистика</div>

      <div class="sec-head"><div class="s-title">Активность по неделям</div></div>
      <div class="bars">
        ${weeks.map(w=>{
          const total = w.sub+w.int+w.rej+w.off;
          const h = total/maxTotal*80;
          const ph = p => (p/total||0)*h;
          return `<div class="bar-col">
            <div class="bar-total">${total||''}</div>
            <div class="bar-stack" style="height:${h}px">
              ${w.off?`<div class="bar-seg" style="height:${ph(w.off)}px;background:#1E9D5B"></div>`:''}
              ${w.int?`<div class="bar-seg" style="height:${ph(w.int)}px;background:var(--accent)"></div>`:''}
              ${w.rej?`<div class="bar-seg" style="height:${ph(w.rej)}px;background:#C03535"></div>`:''}
              ${w.sub?`<div class="bar-seg" style="height:${ph(w.sub)}px;background:#8E8E93"></div>`:''}
            </div>
            <div class="bar-label">${w.l}</div>
          </div>`;
        }).join('')}
      </div>
      <div class="legend">
        <div class="lg"><span class="lg-sw" style="background:#8E8E93"></span>Подано</div>
        <div class="lg"><span class="lg-sw" style="background:var(--accent)"></span>Интервью</div>
        <div class="lg"><span class="lg-sw" style="background:#C03535"></span>Отказ</div>
        <div class="lg"><span class="lg-sw" style="background:#1E9D5B"></span>Оффер</div>
      </div>

      <div class="sec-head" style="margin-top:8px"><div class="s-title">Воронка по этапам</div></div>
      <div class="funnel">
        ${funnel.map(f=>`<div class="funnel-row">
          <span class="fn-label">${f.l}</span>
          <span class="fn-bar ${f.cls}" style="width:${f.pct}%">${f.n}</span>
          <span class="fn-pct">${f.pct}%</span>
        </div>`).join('')}
      </div>

      <div class="sec-head" style="margin-top:8px"><div class="s-title">Топ причин отказов</div></div>
      <div class="reasons">
        ${[['HR-скрининг: общие ответы',3],['Кейс: не структурирован',2],['Тестовое: слабый SQL',1],['Скрининг: нет релевантного опыта',1]].map(([l,n])=>`
          <div class="reason">
            <span>${l}</span>
            <div class="r-bar"><span style="width:${n/3*100}%"></span></div>
            <span class="r-count">${n}</span>
          </div>
        `).join('')}
      </div>

      <div class="ai">
        <div class="ai-label">Вывод AI</div>
        <p>Основная зона роста — HR-скрининг. 3 из 7 отказов на этом этапе, общая проблема — слишком общие ответы. В Подготовке уже открыт модуль «STAR-метод», пройди до конца недели.</p>
      </div>
    </div>
  </div>`;
}};

/* G-5 */
const G5={id:'G-5',name:'Достижения · лига',render(s){
  const BADGES=[
    ['🎯','Первый отклик','earned','За первый подтверждённый отклик'],
    ['🔥','7 дней подряд','earned','Неделя подряд активности'],
    ['🧩','5 кейсов','earned','5 AI-тренажёров по кейсам'],
    ['📝','Первый mock','earned','Закончил mock-интервью'],
    ['⭐','Mock 80+','locked','Mock с оценкой 80 или выше'],
    ['💼','Первый оффер','locked','Получил первый оффер'],
    ['📚','10 модулей','locked','Закрыл 10 модулей подготовки'],
    ['🏆','30 откликов','locked','Подал 30 откликов'],
    ['🎓','Все треки','locked','Закрыл все 4 трека'],
  ];
  const LEAGUE=[
    {r:1,n:'Анна М.',p:1860,cls:'top1'},
    {r:2,n:'Марк К.',p:1420,cls:'top2'},
    {r:3,n:'Елена С.',p:1180,cls:'top3'},
    {r:4,n:'Ты',p:840,me:true},
    {r:5,n:'Пётр В.',p:790},
    {r:6,n:'Саша Н.',p:660},
    {r:7,n:'Мария Д.',p:540},
  ];
  s.achTab = s.achTab || 'badges';
  return `
  <div class="screen active has-tabbar" data-id="G-5">
    <div class="s-head">
      <button class="back" data-go="G-1">${ICON.back}</button>
      <div class="pill">Достижения</div>
    </div>
    <div class="segment">
      <button class="${s.achTab==='badges'?'active':''}" data-at="badges">Бейджи</button>
      <button class="${s.achTab==='league'?'active':''}" data-at="league">Лига курса</button>
    </div>
    <div class="screen-scroll">
      ${s.achTab==='badges' ? `
        <div style="font-size:12.5px;color:var(--ink-2)">4 из ${BADGES.length} получено</div>
        <div class="badges">
          ${BADGES.map(([ic,n,st,sub])=>`
            <div class="badge ${st}">
              <div class="b-ic">${ic}</div>
              <div class="b-name">${n}</div>
            </div>`).join('')}
        </div>
        <div class="ai" style="margin-top:4px">
          <div class="ai-label">Ближайшая цель</div>
          <p>«Mock 80+» — сейчас лучший результат 78. Один-два повторных mock-прохода, и бейдж твой.</p>
        </div>
      ` : `
        <div class="league-me">
          <div class="lg-rank" style="background:var(--accent);color:#fff">4</div>
          <div style="flex:1">
            <div style="font-weight:600;font-size:14px">Твоё место — 4-е из 38</div>
            <div style="font-size:11.5px;color:var(--accent);opacity:.8">+320 очков до топ-3</div>
          </div>
          <div style="font-weight:600;color:var(--accent);font-variant-numeric:tabular-nums">840</div>
        </div>
        <div style="background:#fff;border:1px solid var(--line);border-radius:12px;margin-top:4px">
          ${LEAGUE.map(x=>`
            <div class="league-row ${x.me?'me':''} ${x.cls||''}">
              <div class="lg-rank">${x.r}</div>
              <div class="lg-name">${esc(x.n)}</div>
              <div class="lg-pts">${x.p} очк.</div>
            </div>`).join('')}
        </div>
        <div style="font-size:11.5px;color:var(--ink-2);text-align:center;margin-top:6px">
          Лига Бизнес-информатики · обновляется раз в неделю
        </div>
      `}
    </div>
  </div>`;
},bind(r,s,a){
  r.querySelectorAll('[data-at]').forEach(el=>el.addEventListener('click',()=>{s.achTab=el.dataset.at;a.rerender()}));
}};

return [G1,G2,G3,G4,G5];
})();
