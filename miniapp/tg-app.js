/* ============================================================
   Stazhka Mini App — SPA shell
   Hash-роутер, lazy-load скриптов секций, mount/unmount,
   мост к Telegram WebApp SDK.
   ============================================================ */
(function(){
  // ---- SectionRegistry (заполняется engine-скриптами по мере загрузки) ----
  const Sections = (() => {
    const map = new Map();
    return {
      register(id, ctx){ map.set(id, ctx); },
      get(id){ return map.get(id); },
      has(id){ return map.has(id); }
    };
  })();
  window.SectionRegistry = Sections;
  window.SPA_MODE = true;

  // ---- Telegram SDK ----
  const tg = window.Telegram && window.Telegram.WebApp;
  if(tg){
    try {
      tg.ready();
      tg.expand();
      tg.setHeaderColor && tg.setHeaderColor('#7A1B1B');
      tg.setBackgroundColor && tg.setBackgroundColor('#ffffff');
      tg.disableVerticalSwipes && tg.disableVerticalSwipes();
      // MainButton — фиксируем фирменный цвет, дальше только меняем текст
      if(tg.MainButton){
        tg.MainButton.setParams({ color: '#7A1B1B', text_color: '#ffffff' });
        tg.MainButton.hide();
      }
      console.log('TG colorScheme:', tg.colorScheme);
    } catch(e){ console.warn('TG init', e); }
  }

  // ---- Префилл ФИО из tg.initDataUnsafe.user ----
  // Если Telegram передал имя/фамилию и в Store пусто — заполняем.
  // Юзер всё равно увидит онбординг, но шаг ФИО будет с предзаполненным значением.
  (function prefillFromTelegram(){
    if(!tg || !tg.initDataUnsafe) return;
    const u = tg.initDataUnsafe.user;
    if(!u || !u.first_name) return;
    const cur = window.Store.get();
    if(cur.user.fio && cur.user.fio.trim()) return;
    const full = [u.first_name, u.last_name].filter(Boolean).join(' ').trim();
    if(full) window.Store.update({ user: { fio: full } });
  })();

  // ---- Описание секций ----
  const ICONS = {
    search:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    prep:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 19.5V6a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2z"/><path d="M8 8h8M8 12h6"/></svg>',
    progress: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/></svg>',
    chat:     '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8z"/></svg>',
    profile:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>'
  };

  const SECTIONS = [
    { id:'onboarding', label:'Онбординг',  defaultScreen:'O-1', scripts:['proto-screens.js','proto-engine.js'],     showInTabs:false },
    { id:'search',     label:'Поиск',      defaultScreen:'S-1', scripts:['search-screens.js','search-engine.js'],   showInTabs:true,  icon:ICONS.search   },
    { id:'prep',       label:'Подготовка', defaultScreen:'P-1', scripts:['prep-screens.js','prep-engine.js'],       showInTabs:true,  icon:ICONS.prep     },
    { id:'progress',   label:'Прогресс',   defaultScreen:'G-1', scripts:['progress-screens.js','progress-engine.js'], showInTabs:true, icon:ICONS.progress },
    { id:'chat',       label:'Чат',        defaultScreen:'C-1', scripts:['chat-screens.js','chat-engine.js'],       showInTabs:true,  icon:ICONS.chat     },
    { id:'profile',    label:'Профиль',    defaultScreen:'U-1', scripts:['profile-screens.js','profile-engine.js'], showInTabs:true,  icon:ICONS.profile  }
  ];
  const sectionById = Object.fromEntries(SECTIONS.map(s => [s.id, s]));

  // ---- DOM ----
  const splash = document.getElementById('splash');
  const stage = document.getElementById('stage');
  const view = document.getElementById('view');
  const tabbar = document.getElementById('tabbar');

  // ---- Tabbar render ----
  tabbar.innerHTML = SECTIONS.filter(s => s.showInTabs).map(s => `
    <button class="tg-tab" data-id="${s.id}" type="button">
      ${s.icon}
      <span>${s.label}</span>
    </button>
  `).join('');
  tabbar.querySelectorAll('.tg-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      if(tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
      navigate(btn.dataset.id);
    });
  });

  // ---- Lazy script loader ----
  const loadedScripts = new Set();
  function loadScript(src){
    if(loadedScripts.has(src)) return Promise.resolve();
    return new Promise((res, rej) => {
      const s = document.createElement('script');
      s.src = src;
      s.onload = () => { loadedScripts.add(src); res(); };
      s.onerror = () => rej(new Error('load failed: ' + src));
      document.head.appendChild(s);
    });
  }
  async function loadSection(sec){
    for(const src of sec.scripts) await loadScript(src);
  }

  // ---- Activation ----
  let currentSectionId = null;
  async function activate(sectionId, screenId){
    const sec = sectionById[sectionId];
    if(!sec){
      activate(window.Store.get().meta.onboardingDone ? 'search' : 'onboarding');
      return;
    }
    if(sectionId === currentSectionId){
      // Та же секция — просто навигируем на нужный экран внутри
      const ctx = Sections.get(sectionId);
      if(screenId && ctx && ctx.goTo) ctx.goTo(screenId);
      updateBackButton(sectionId, screenId);
      return;
    }

    splash.classList.remove('gone');

    try {
      await loadSection(sec);
    } catch(e){
      console.error('section load failed', e);
      splash.classList.add('gone');
      return;
    }

    // Размонтировать предыдущую
    if(currentSectionId){
      const prev = Sections.get(currentSectionId);
      if(prev && prev.unmount) prev.unmount();
    }

    // Состояние табов и UI
    tabbar.querySelectorAll('.tg-tab').forEach(b => {
      b.classList.toggle('on', b.dataset.id === sectionId);
    });
    document.body.classList.toggle('section-onboarding', sectionId === 'onboarding');

    // Монтирование
    view.innerHTML = '';
    const ctx = Sections.get(sectionId);
    if(ctx && ctx.mount){
      ctx.mount(view, screenId || sec.defaultScreen);
    } else {
      console.warn('section not registered:', sectionId);
    }
    currentSectionId = sectionId;

    setTimeout(() => splash.classList.add('gone'), 80);
    updateBackButton(sectionId, screenId);
  }

  // ---- Telegram BackButton ----
  function updateBackButton(sectionId, screenId){
    if(!tg || !tg.BackButton) return;
    const sec = sectionById[sectionId];
    const isRoot = !screenId || screenId === (sec && sec.defaultScreen);
    if(isRoot){
      tg.BackButton.hide();
    } else {
      tg.BackButton.show();
    }
  }
  if(tg && tg.BackButton){
    tg.BackButton.onClick(() => {
      if(history.length > 1){
        history.back();
      } else {
        navigate('search');
      }
    });
  }

  // ---- Telegram MainButton ----
  // Движок может попросить shell показать primary CTA через MainButton.
  // Сейчас mirroring включён только для онбординга (там самый чёткий CTA "Далее").
  let mainButtonHandler = null;
  function setMainButton(opts){
    if(!tg || !tg.MainButton) return;
    const mb = tg.MainButton;
    if(!opts){ clearMainButton(); return; }
    mb.setText(opts.text || 'Далее');
    if(opts.color) mb.setParams({ color: opts.color });
    if(mainButtonHandler) mb.offClick(mainButtonHandler);
    mainButtonHandler = typeof opts.onClick === 'function' ? opts.onClick : null;
    if(mainButtonHandler) mb.onClick(mainButtonHandler);
    if(opts.disabled){
      mb.disable && mb.disable();
    } else {
      mb.enable && mb.enable();
    }
    mb.show();
  }
  function clearMainButton(){
    if(!tg || !tg.MainButton) return;
    const mb = tg.MainButton;
    if(mainButtonHandler){ mb.offClick(mainButtonHandler); mainButtonHandler = null; }
    mb.hide();
  }

  // ---- Хук, который движки дёргают после render() ----
  // Обновляет BackButton под текущий экран и (для онбординга) мирроринг primary CTA на MainButton.
  function onScreenRendered(sectionId, screenId, viewEl){
    updateBackButton(sectionId, screenId);

    if(sectionId === 'onboarding' && viewEl){
      // Ищем primary .btn (не ghost / не outline / не back / не reset / не jump)
      const candidates = viewEl.querySelectorAll('.btn:not(.ghost):not(.outline)');
      let primary = null;
      for(const el of candidates){
        const act = el.dataset.act;
        if(act === 'back' || act === 'reset' || act === 'jump') continue;
        primary = el;
        break;
      }
      if(primary){
        const text = (primary.textContent || 'Далее').trim();
        const disabled = primary.getAttribute('aria-disabled') === 'true';
        setMainButton({ text, disabled, onClick: () => { if(!disabled) primary.click(); } });
        return;
      }
    }
    clearMainButton();
  }

  // ---- Haptic feedback на тапы по интерактиву ----
  // Делегируем один раз на view; при каждом render() viewEl остаётся тем же DOM-узлом.
  view.addEventListener('click', (e) => {
    if(!tg || !tg.HapticFeedback) return;
    const t = e.target.closest('.chip, .btn, [data-go], [data-act], .rowbtn, .vacancy, .module, .track, .tab, .toggle');
    if(t) {
      try { tg.HapticFeedback.impactOccurred('light'); } catch(err){}
    }
  });

  // ---- Hash router ----
  // #<section>/<screenId>
  function parseHash(){
    const h = decodeURIComponent(location.hash.replace(/^#/, ''));
    if(!h) return { sectionId: null, screenId: null };
    const [sec, ...rest] = h.split('/');
    return { sectionId: sec || null, screenId: rest.join('/') || null };
  }
  function navigate(sectionId, screenId){
    const target = '#' + sectionId + (screenId ? '/' + screenId : '');
    if(location.hash !== target){
      location.hash = target; // вызовет hashchange → activate
    } else {
      activate(sectionId, screenId);
    }
  }
  window.addEventListener('hashchange', () => {
    const { sectionId, screenId } = parseHash();
    if(sectionId && sectionById[sectionId]){
      activate(sectionId, screenId);
    }
  });

  // ---- Initial ----
  const initial = (() => {
    const fromHash = parseHash();
    if(fromHash.sectionId && sectionById[fromHash.sectionId]) return fromHash;
    return window.Store.get().meta.onboardingDone
      ? { sectionId: 'search', screenId: null }
      : { sectionId: 'onboarding', screenId: null };
  })();
  history.replaceState(null, '', '#' + initial.sectionId + (initial.screenId ? '/' + initial.screenId : ''));
  activate(initial.sectionId, initial.screenId);

  // ---- Public ----
  window.StazhkaApp = {
    navigate,
    activate,
    sections: SECTIONS,
    tg,
    // SDK-мост для движков
    setMainButton,
    clearMainButton,
    onScreenRendered,
    haptic(kind){
      if(!tg || !tg.HapticFeedback) return;
      try {
        if(kind === 'success' || kind === 'warning' || kind === 'error'){
          tg.HapticFeedback.notificationOccurred(kind);
        } else if(kind === 'select'){
          tg.HapticFeedback.selectionChanged();
        } else {
          tg.HapticFeedback.impactOccurred(kind || 'light');
        }
      } catch(e){}
    }
  };
})();
