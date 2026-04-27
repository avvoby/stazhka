/* Profile tab — U-1..U-9 */
window.ProfileScreens = (function(){
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}

const ICON={
  back:'<svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg>',
  chev:'<svg viewBox="0 0 24 24"><path d="m9 6 6 6-6 6"/></svg>',
  edit:'<svg viewBox="0 0 24 24"><path d="M17 3 21 7 8 20H4v-4z"/></svg>',
  cv:'<svg viewBox="0 0 24 24"><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/></svg>',
  skill:'<svg viewBox="0 0 24 24"><path d="m12 3 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"/></svg>',
  exp:'<svg viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>',
  edu:'<svg viewBox="0 0 24 24"><path d="m12 3 10 5-10 5L2 8zM6 10v5c0 2 3 4 6 4s6-2 6-4v-5"/></svg>',
  bell:'<svg viewBox="0 0 24 24"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9Z"/><path d="M10 21a2 2 0 0 0 4 0"/></svg>',
  lock:'<svg viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/></svg>',
  star:'<svg viewBox="0 0 24 24"><path d="m12 3 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z"/></svg>',
  help:'<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 6 0c0 2-3 2-3 4M12 17v.01"/></svg>',
  logout:'<svg viewBox="0 0 24 24"><path d="M15 12H3M8 7l-5 5 5 5M15 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/></svg>',
  check:'<svg viewBox="0 0 24 24"><path d="M5 12l4 4L19 7"/></svg>',
  x:'<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
  plus:'<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
  share:'<svg viewBox="0 0 24 24"><path d="M4 12v7a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-7M16 6l-4-4-4 4M12 2v14"/></svg>',
};

/* ---------- U-1: Профиль · главная ---------- */
const U1={id:'U-1',name:'Профиль · главная',render(s){
  return `
  <div class="screen active has-tabbar" data-id="U-1" style="padding:0">
    <div class="profile-hero" style="margin:0;padding:20px 20px 52px">
      <div class="ph-edit" data-go="U-3">${ICON.edit}</div>
      <div class="avatar">ИИ</div>
      <div class="ph-name">Иван Иванов</div>
      <div class="ph-sub">НИУ ВШЭ · Бизнес-информатика · 3 курс</div>
    </div>
    <div style="padding:0 20px 16px;margin-top:-32px;position:relative;z-index:2;display:flex;flex-direction:column;gap:10px">
      <div class="quick-stats" style="margin:0">
        <div class="qs"><div class="qs-num">7</div><div class="qs-label">откликов</div></div>
        <div class="qs"><div class="qs-num">12</div><div class="qs-label">дней streak</div></div>
        <div class="qs"><div class="qs-num">840</div><div class="qs-label">очков</div></div>
      </div>

      <div class="group-title">Резюме и профиль</div>
      <div class="menu">
        <div class="menu-item" data-go="U-2">
          <div class="mi-icon">${ICON.cv}</div>
          <div class="mi-body"><div class="mi-label">Резюме</div><div class="mi-sub">Обновлено вчера · 1 версия</div></div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item" data-go="U-4">
          <div class="mi-icon">${ICON.skill}</div>
          <div class="mi-body"><div class="mi-label">Навыки</div><div class="mi-sub">12 навыков · 3 предложения от AI</div></div>
          <div class="mi-badge">3</div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item" data-go="U-5">
          <div class="mi-icon">${ICON.exp}</div>
          <div class="mi-body"><div class="mi-label">Опыт и проекты</div><div class="mi-sub">2 записи · добавь 3-й проект</div></div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item" data-go="U-6">
          <div class="mi-icon">${ICON.edu}</div>
          <div class="mi-body"><div class="mi-label">Образование</div><div class="mi-sub">ВШЭ · 3 курс</div></div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
      </div>

      <div class="group-title">Приложение</div>
      <div class="menu">
        <div class="menu-item" data-go="U-7">
          <div class="mi-icon">${ICON.bell}</div>
          <div class="mi-body"><div class="mi-label">Уведомления</div><div class="mi-sub">Push, фоллоу-апы, дайджест</div></div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item" data-go="U-8">
          <div class="mi-icon">${ICON.lock}</div>
          <div class="mi-body"><div class="mi-label">Приватность и данные</div><div class="mi-sub">Что видит работодатель, экспорт</div></div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item" data-go="U-9">
          <div class="mi-icon" style="background:var(--accent-2);color:var(--accent)">${ICON.star}</div>
          <div class="mi-body"><div class="mi-label">Стажка Pro</div><div class="mi-sub">AI без лимитов, mock без очереди</div></div>
          <div class="mi-val">Free</div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
      </div>

      <div class="group-title">Поддержка</div>
      <div class="menu">
        <div class="menu-item">
          <div class="mi-icon">${ICON.help}</div>
          <div class="mi-body"><div class="mi-label">Помощь и обратная связь</div></div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item" style="color:#C03535">
          <div class="mi-icon" style="color:#C03535">${ICON.logout}</div>
          <div class="mi-body"><div class="mi-label">Выйти</div></div>
        </div>
      </div>

      <div style="text-align:center;font-size:11px;color:var(--ink-2);padding:8px 0 4px">
        Стажка · версия 1.0.4
      </div>
    </div>
  </div>`;
}};

/* ---------- U-2: Резюме · просмотр ---------- */
const U2={id:'U-2',name:'Резюме · просмотр',render(s){
  return `
  <div class="screen active has-tabbar" data-id="U-2">
    <div class="s-head">
      <button class="back" data-go="U-1">${ICON.back}</button>
      <div class="pill">Резюме</div>
      <div style="margin-left:auto;cursor:pointer;color:var(--ink);padding:4px" title="Поделиться">${ICON.share}</div>
    </div>
    <div class="screen-scroll">
      <div class="paper">
        <div class="p-name">Иванов Иван Иванович</div>
        <div class="p-contact">ivan.ivanov@edu.hse.ru · +7 999 123-45-67 · Москва</div>

        <div class="p-sec">
          <div class="p-sec-title">О себе</div>
          <div class="p-entry-body">Студент 3 курса Бизнес-информатики ВШЭ. Ищу стажировку аналитика в консалтинге или банке. Сильный Excel, базовый SQL, прошёл курс по кейс-интервью.</div>
        </div>

        <div class="p-sec">
          <div class="p-sec-title">Образование</div>
          <div class="p-entry">
            <div class="p-entry-top"><span>НИУ ВШЭ, Москва</span><span>2023 — н.в.</span></div>
            <div class="p-entry-sub">Бизнес-информатика, бакалавриат · GPA 8.7/10</div>
          </div>
        </div>

        <div class="p-sec">
          <div class="p-sec-title">Опыт и проекты</div>
          <div class="p-entry">
            <div class="p-entry-top"><span>Аналитический проект «Пятёрочка»</span><span>2024</span></div>
            <div class="p-entry-sub">Учебный кейс, команда из 4</div>
            <ul>
              <li>Собрал данные по 200+ магазинам через публичные источники</li>
              <li>Построил дашборд в Excel c метриками оттока клиентов</li>
              <li>Презентовал выводы перед преподавателем из SBS</li>
            </ul>
          </div>
          <div class="p-entry">
            <div class="p-entry-top"><span>Волонтёр в СтудСовете</span><span>2023 — н.в.</span></div>
            <div class="p-entry-sub">Организация HR-дней, 6 мероприятий</div>
          </div>
        </div>

        <div class="p-sec">
          <div class="p-sec-title">Навыки</div>
          <div class="p-entry-body">Excel (уверенно), SQL (базово), PowerPoint, финансовые модели, английский B2</div>
        </div>
      </div>

      <div class="ai">
        <div class="ai-label">AI заметил</div>
        <p>Резюме короткое и чистое — хорошо. Но в разделе «Опыт» мало цифр. Добавь 1-2 метрики к проекту «Пятёрочка» (сколько клиентов в выборке, какой рост метрики ты нашёл) — это заметно поднимет конверсию скрининга.</p>
      </div>

      <button class="btn" data-go="U-3">Редактировать с AI</button>
      <button class="btn ghost">Скачать PDF</button>
    </div>
  </div>`;
}};

/* ---------- U-3: Редактор резюме ---------- */
const U3={id:'U-3',name:'Резюме · редактор',render(s){
  return `
  <div class="screen active has-tabbar" data-id="U-3">
    <div class="s-head">
      <button class="back" data-go="U-2">${ICON.back}</button>
      <div class="pill">Редактор резюме</div>
    </div>
    <div class="screen-scroll">
      <div class="title" style="font-size:22px">Секции</div>

      <div class="edit-row" data-go="U-3">
        <div class="er-icon">${ICON.cv}</div>
        <div class="er-body">
          <div class="er-label">О себе</div>
          <div class="er-val">Студент 3 курса Бизнес-информатики ВШЭ. Ищу стажировку…</div>
        </div>
        <div class="mi-chev">${ICON.chev}</div>
      </div>

      <div class="edit-row" data-go="U-6">
        <div class="er-icon">${ICON.edu}</div>
        <div class="er-body">
          <div class="er-label">Образование</div>
          <div class="er-val">ВШЭ · Бизнес-информатика · GPA 8.7</div>
        </div>
        <div class="mi-chev">${ICON.chev}</div>
      </div>

      <div class="edit-row" data-go="U-5">
        <div class="er-icon">${ICON.exp}</div>
        <div class="er-body">
          <div class="er-label">Опыт и проекты</div>
          <div class="er-val">2 записи · AI советует добавить 1 проект</div>
        </div>
        <div class="mi-chev">${ICON.chev}</div>
      </div>

      <div class="edit-row" data-go="U-4">
        <div class="er-icon">${ICON.skill}</div>
        <div class="er-body">
          <div class="er-label">Навыки</div>
          <div class="er-val">12 навыков · 3 предложения от AI</div>
        </div>
        <div class="mi-chev">${ICON.chev}</div>
      </div>

      <div class="edit-row">
        <div class="er-icon">${ICON.plus}</div>
        <div class="er-body">
          <div class="er-label" style="color:var(--accent)">Добавить секцию</div>
          <div class="er-val">Сертификаты, языки, волонтёрство</div>
        </div>
      </div>

      <div class="ai">
        <div class="ai-label">AI-ассистент</div>
        <p>Могу переписать «О себе» под конкретную вакансию. Выбери отклик, к которому подгонять — и я сделаю 2 варианта текста.</p>
      </div>
      <button class="btn">Переписать под вакансию</button>
    </div>
  </div>`;
}};

/* ---------- U-4: Мои навыки ---------- */
const U4={id:'U-4',name:'Навыки',render(s){
  s.hardTags = s.hardTags || ['Excel','SQL','PowerPoint','Финмодели','HTML/CSS','Python (база)','R (база)'];
  s.softTags = s.softTags || ['Презентации','Командная работа','Английский B2','Тайм-менеджмент','Инициативность'];
  s.aiSuggest = s.aiSuggest || ['Power BI','Storytelling','Деловая переписка'];
  return `
  <div class="screen active has-tabbar" data-id="U-4">
    <div class="s-head">
      <button class="back" data-go="U-1">${ICON.back}</button>
      <div class="pill">Навыки</div>
    </div>
    <div class="screen-scroll">
      <div class="group-title">Hard skills · ${s.hardTags.length}</div>
      <div class="tags">
        ${s.hardTags.map(t=>`<span class="tag">${esc(t)} <span class="x" data-rm-hard="${esc(t)}">×</span></span>`).join('')}
        <span class="tag adding" data-act="add-hard">+ добавить</span>
      </div>

      <div class="group-title" style="margin-top:14px">Soft skills · ${s.softTags.length}</div>
      <div class="tags">
        ${s.softTags.map(t=>`<span class="tag">${esc(t)} <span class="x" data-rm-soft="${esc(t)}">×</span></span>`).join('')}
        <span class="tag adding" data-act="add-soft">+ добавить</span>
      </div>

      ${s.aiSuggest.length ? `
      <div class="ai" style="margin-top:16px">
        <div class="ai-label">AI советует добавить · ${s.aiSuggest.length}</div>
        <p style="margin-bottom:8px">Частые навыки для твоих целевых вакансий, которых нет в профиле:</p>
        <div class="tags">
          ${s.aiSuggest.map(t=>`<span class="tag ai">${esc(t)} <span class="x" data-add-ai="${esc(t)}">+</span></span>`).join('')}
        </div>
      </div>` : `
      <div class="ai" style="margin-top:16px">
        <div class="ai-label">Отлично</div>
        <p>Все рекомендованные навыки добавлены. AI пересчитает подборку с учётом новых тегов.</p>
      </div>
      `}
    </div>
  </div>`;
},bind(r,s,a){
  r.querySelectorAll('[data-rm-hard]').forEach(el=>el.addEventListener('click',(e)=>{e.stopPropagation();s.hardTags=s.hardTags.filter(x=>x!==el.dataset.rmHard);a.rerender()}));
  r.querySelectorAll('[data-rm-soft]').forEach(el=>el.addEventListener('click',(e)=>{e.stopPropagation();s.softTags=s.softTags.filter(x=>x!==el.dataset.rmSoft);a.rerender()}));
  r.querySelectorAll('[data-add-ai]').forEach(el=>el.addEventListener('click',()=>{
    const t = el.dataset.addAi;
    if(!s.hardTags.includes(t)) s.hardTags.push(t);
    s.aiSuggest = s.aiSuggest.filter(x=>x!==t);
    a.rerender();
  }));
  r.querySelectorAll('[data-act="add-hard"]').forEach(el=>el.addEventListener('click',()=>{
    const t = prompt('Навык:'); if(t && !s.hardTags.includes(t)) { s.hardTags.push(t); a.rerender(); }
  }));
  r.querySelectorAll('[data-act="add-soft"]').forEach(el=>el.addEventListener('click',()=>{
    const t = prompt('Навык:'); if(t && !s.softTags.includes(t)) { s.softTags.push(t); a.rerender(); }
  }));
}};

/* ---------- U-5: Опыт и проекты ---------- */
const U5={id:'U-5',name:'Опыт и проекты',render(s){
  const EXP=[
    {logo:'П',role:'Аналитик-волонтёр',company:'Учебный проект «Пятёрочка»',date:'окт 2024 — н.в.',desc:'Сбор данных, дашборд в Excel, защита перед SBS. 200+ магазинов, модель оттока.'},
    {logo:'С',role:'Член СтудСовета',company:'НИУ ВШЭ',date:'сен 2023 — н.в.',desc:'Организация HR-дней и ярмарок вакансий, 6 мероприятий, 400+ участников.'},
  ];
  return `
  <div class="screen active has-tabbar" data-id="U-5">
    <div class="s-head">
      <button class="back" data-go="U-1">${ICON.back}</button>
      <div class="pill">Опыт и проекты</div>
    </div>
    <div class="screen-scroll">
      ${EXP.map(e=>`
        <div class="exp-item">
          <div class="exp-logo">${e.logo}</div>
          <div class="exp-body">
            <div class="exp-role">${esc(e.role)}</div>
            <div class="exp-company">${esc(e.company)}</div>
            <div class="exp-date">${esc(e.date)}</div>
            <div class="exp-desc">${esc(e.desc)}</div>
          </div>
        </div>`).join('')}

      <button class="btn ghost"><span style="margin-right:6px">+</span>Добавить опыт или проект</button>

      <div class="ai">
        <div class="ai-label">AI-совет</div>
        <p>Два проекта — достаточный минимум, но для консалтинга и банков лучше три. У тебя в профиле указан курс по кейс-интервью — оформи это отдельной записью с результатом («финал учебного кейс-чемпионата»).</p>
      </div>
    </div>
  </div>`;
}};

/* ---------- U-6: Образование ---------- */
const U6={id:'U-6',name:'Образование',render(s){
  return `
  <div class="screen active has-tabbar" data-id="U-6">
    <div class="s-head">
      <button class="back" data-go="U-1">${ICON.back}</button>
      <div class="pill">Образование</div>
    </div>
    <div class="screen-scroll">
      <div class="group-title">Основное</div>
      <div class="paper">
        <div class="p-entry-top"><span style="font-weight:600">НИУ ВШЭ</span><span>2023 — 2027</span></div>
        <div class="p-entry-sub">Школа бизнеса и делового администрирования · бакалавриат</div>
        <div class="p-entry-sub" style="margin-top:8px;color:var(--ink)">Программа: Бизнес-информатика · 3 курс · GPA 8.7/10</div>
      </div>

      <div class="group-title" style="margin-top:12px">Дополнительное</div>
      <div class="menu">
        <div class="menu-item">
          <div class="mi-icon">${ICON.edu}</div>
          <div class="mi-body">
            <div class="mi-label">Курс «Кейс-интервью для стажёра»</div>
            <div class="mi-sub">Changellenge · 2024 · сертификат</div>
          </div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item">
          <div class="mi-icon">${ICON.edu}</div>
          <div class="mi-body">
            <div class="mi-label">Школа юного аналитика</div>
            <div class="mi-sub">Сбер · лето 2023</div>
          </div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
      </div>

      <button class="btn ghost">Добавить курс или сертификат</button>
    </div>
  </div>`;
}};

/* ---------- U-7: Уведомления ---------- */
const U7={id:'U-7',name:'Уведомления',render(s){
  s.notif = s.notif || {
    newVac:true, alerts:true, followup:true, digest:true,
    chat:true, email:false, reject:true
  };
  const sw = (k,label,sub)=>`
    <div class="switch" data-sw="${k}">
      <div class="sw-body">
        <div class="sw-label">${label}</div>
        <div class="sw-sub">${sub}</div>
      </div>
      <div class="toggle-ui ${s.notif[k]?'on':''}"></div>
    </div>`;
  return `
  <div class="screen active has-tabbar" data-id="U-7">
    <div class="s-head">
      <button class="back" data-go="U-1">${ICON.back}</button>
      <div class="pill">Уведомления</div>
    </div>
    <div class="screen-scroll">
      <div class="group-title">Про вакансии</div>
      <div>
        ${sw('newVac','Новые подходящие вакансии','Когда AI находит вакансию с match > 80%')}
        ${sw('alerts','Алерты по компаниям','Уведомление при открытии стажировки в твоих компаниях')}
      </div>

      <div class="group-title">Про отклики</div>
      <div>
        ${sw('followup','Напоминания о фоллоу-апе','Через 7 дней после отклика')}
        ${sw('reject','Помощь при отказе','Предложить дневник и разбор с AI')}
      </div>

      <div class="group-title">Общее</div>
      <div>
        ${sw('digest','Недельный дайджест','По воскресеньям, итоги недели')}
        ${sw('chat','Сообщения от AI-наставника','Новые сообщения в чате')}
      </div>

      <div class="group-title">Каналы доставки</div>
      <div>
        ${sw('email','Email-копия','Дублировать важное на e-mail')}
      </div>
    </div>
  </div>`;
},bind(r,s,a){
  r.querySelectorAll('[data-sw]').forEach(el=>el.addEventListener('click',()=>{
    const k = el.dataset.sw;
    s.notif[k] = !s.notif[k];
    a.rerender();
  }));
}};

/* ---------- U-8: Приватность ---------- */
const U8={id:'U-8',name:'Приватность и данные',render(s){
  s.privacy = s.privacy || { showPhone:false, showGpa:true, showProjects:true, anon:false };
  const sw = (k,label,sub)=>`
    <div class="switch" data-sw="${k}">
      <div class="sw-body">
        <div class="sw-label">${label}</div>
        <div class="sw-sub">${sub}</div>
      </div>
      <div class="toggle-ui ${s.privacy[k]?'on':''}"></div>
    </div>`;
  return `
  <div class="screen active has-tabbar" data-id="U-8">
    <div class="s-head">
      <button class="back" data-go="U-1">${ICON.back}</button>
      <div class="pill">Приватность и данные</div>
    </div>
    <div class="screen-scroll">
      <div class="group-title">Что видит работодатель</div>
      <div>
        ${sw('showPhone','Показывать телефон','Без него работодатель напишет в чат Стажки')}
        ${sw('showGpa','Показывать GPA','Средний балл в резюме')}
        ${sw('showProjects','Показывать проекты','Разделы «Опыт» и «Сертификаты»')}
        ${sw('anon','Анонимный режим поиска','Работодатель видит профиль только после отклика')}
      </div>

      <div class="group-title">Превью резюме для работодателя</div>
      <div class="preview-card">
        <div class="pv-label">Как видит HR</div>
        <div class="pv-field"><b>Имя</b><span>Иван И.</span></div>
        <div class="pv-field ${s.privacy.showPhone?'':'hidden'}"><b>Телефон</b><span>${s.privacy.showPhone?'+7 999 123-45-67':'скрыт'}</span></div>
        <div class="pv-field"><b>Email</b><span>i***v@edu.hse.ru</span></div>
        <div class="pv-field"><b>Университет</b><span>НИУ ВШЭ, 3 курс</span></div>
        <div class="pv-field ${s.privacy.showGpa?'':'hidden'}"><b>GPA</b><span>${s.privacy.showGpa?'8.7/10':'скрыт'}</span></div>
        <div class="pv-field ${s.privacy.showProjects?'':'hidden'}"><b>Проекты</b><span>${s.privacy.showProjects?'2 записи':'скрыто'}</span></div>
      </div>

      <div class="group-title" style="margin-top:12px">Данные</div>
      <div class="menu">
        <div class="menu-item">
          <div class="mi-icon">${ICON.share}</div>
          <div class="mi-body"><div class="mi-label">Экспорт всех данных</div><div class="mi-sub">JSON + PDF резюме</div></div>
          <div class="mi-chev">${ICON.chev}</div>
        </div>
        <div class="menu-item" style="color:#C03535">
          <div class="mi-icon" style="color:#C03535">${ICON.x}</div>
          <div class="mi-body"><div class="mi-label">Удалить аккаунт</div><div class="mi-sub" style="color:#C0353599">Безвозвратно</div></div>
        </div>
      </div>
    </div>
  </div>`;
},bind(r,s,a){
  r.querySelectorAll('[data-sw]').forEach(el=>el.addEventListener('click',()=>{
    const k = el.dataset.sw; s.privacy[k] = !s.privacy[k]; a.rerender();
  }));
}};

/* ---------- U-9: Подписка ---------- */
const U9={id:'U-9',name:'Стажка Pro',render(s){
  const Check = `<div class="check-ic">${ICON.check}</div>`;
  const Dash = `<div class="check-ic">${ICON.x}</div>`;
  return `
  <div class="screen active has-tabbar" data-id="U-9">
    <div class="s-head">
      <button class="back" data-go="U-1">${ICON.back}</button>
      <div class="pill">Тариф</div>
    </div>
    <div class="screen-scroll">
      <div class="title" style="font-size:22px">Стажка Pro</div>
      <div class="subtitle">Больше AI, меньше ожидания, без ограничений</div>

      <div class="plan-card">
        <div class="p-title">Free</div>
        <div class="p-price">0 ₽ <small>/ мес · текущий</small></div>
        <div class="p-feats">
          <div class="p-feat">${Check}Подборка · 10 вакансий/день</div>
          <div class="p-feat">${Check}AI cover letter · 5/день</div>
          <div class="p-feat">${Check}Трекер откликов</div>
          <div class="p-feat off">${Dash}Mock-интервью без очереди</div>
          <div class="p-feat off">${Dash}AI-разбор резюме под вакансию</div>
          <div class="p-feat off">${Dash}Приоритет в подборе</div>
        </div>
      </div>

      <div class="plan-card featured">
        <div class="p-title">Pro</div>
        <div class="p-price">490 ₽ <small>/ мес</small></div>
        <div class="p-feats">
          <div class="p-feat">${Check}Подборка без лимита</div>
          <div class="p-feat">${Check}AI cover letter без лимита</div>
          <div class="p-feat">${Check}Mock-интервью без очереди</div>
          <div class="p-feat">${Check}AI-разбор резюме под каждую вакансию</div>
          <div class="p-feat">${Check}Приоритет в подборе и поддержке</div>
          <div class="p-feat">${Check}Отмена в любой момент</div>
        </div>
        <button class="btn">Попробовать 7 дней бесплатно</button>
        <div style="text-align:center;font-size:11px;color:var(--ink-2);margin-top:-2px">Дальше 490 ₽/мес, можно отменить</div>
      </div>

      <div class="ai" style="margin-top:4px">
        <div class="ai-label">Для студентов ВШЭ</div>
        <p>Активируй через студенческую почту @edu.hse.ru — первые 30 дней Pro бесплатно, без ввода карты.</p>
      </div>
    </div>
  </div>`;
}};

return [U1, U2, U3, U4, U5, U6, U7, U8, U9];
})();
