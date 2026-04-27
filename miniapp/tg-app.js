/* Telegram Mini App — section router + TG SDK glue */
(function(){
  // ---- Telegram SDK ----
  const tg = window.Telegram && window.Telegram.WebApp;
  if(tg){
    try{
      tg.ready();
      tg.expand();
      // We force our own colors regardless of TG theme (consistency for the test)
      tg.setHeaderColor && tg.setHeaderColor('#7A1B1B');
      tg.setBackgroundColor && tg.setBackgroundColor('#ffffff');
      tg.disableVerticalSwipes && tg.disableVerticalSwipes();
    }catch(e){}
  }

  // ---- Sections (each is a full HTML page already living in the project) ----
  const SECTIONS = [
    { id:'onboarding', label:'Онбординг', file:'Stazhka Onboarding.html' },
    { id:'search',     label:'Поиск',     file:'Stazhka Search.html' },
    { id:'prep',       label:'Подготовка',file:'Stazhka Prep.html' },
    { id:'progress',   label:'Прогресс',  file:'Stazhka Progress.html' },
    { id:'chat',       label:'Чат',       file:'Stazhka Chat.html' },
    { id:'profile',    label:'Профиль',   file:'Stazhka Profile.html' },
  ];

  // Onboarding shown first time only
  const KEY_DONE = 'stazhka_onboarding_done_v1';
  function isOnboarded(){ return localStorage.getItem(KEY_DONE) === '1'; }
  function markOnboarded(){ localStorage.setItem(KEY_DONE, '1'); }

  // ---- Tabbar ----
  const tabbar = document.getElementById('tabbar');
  const tabSections = SECTIONS.filter(s => s.id !== 'onboarding');

  const ICONS = {
    search:   '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    prep:     '<svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></svg>',
    progress: '<svg viewBox="0 0 24 24"><path d="M3 3v18h18"/><path d="M7 15l4-4 4 3 5-7"/></svg>',
    chat:     '<svg viewBox="0 0 24 24"><path d="M21 12a8 8 0 0 1-11 7l-4 1 1-4A8 8 0 1 1 21 12Z"/></svg>',
    profile:  '<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-7 8-7s8 3 8 7"/></svg>',
  };

  tabbar.innerHTML = tabSections.map(s => `
    <button class="tg-tab" data-id="${s.id}">
      ${ICONS[s.id] || ''}
      <span>${s.label}</span>
    </button>
  `).join('');

  tabbar.querySelectorAll('.tg-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      if(tg && tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
      goSection(btn.dataset.id);
    });
  });

  // ---- iframe ----
  const frame = document.getElementById('section-frame');
  const splash = document.getElementById('splash');
  let currentId = null;

  function goSection(id){
    const sec = SECTIONS.find(s => s.id === id);
    if(!sec) return;
    if(currentId === id) return;
    currentId = id;

    // Update active tab
    tabbar.querySelectorAll('.tg-tab').forEach(b => {
      b.classList.toggle('on', b.dataset.id === id);
    });

    // Hide tabbar during onboarding
    tabbar.style.display = id === 'onboarding' ? 'none' : '';
    frame.style.bottom = id === 'onboarding' ? '0' : '64px';

    // Update hash (deep links work)
    if(location.hash !== '#' + id) location.hash = id;

    // Load
    splash.classList.remove('gone');
    frame.src = sec.file + '?embed=1';
  }

  frame.addEventListener('load', () => {
    // Strip stage chrome from the embedded section
    try {
      const doc = frame.contentDocument;
      if(doc){
        const css = doc.createElement('style');
        css.textContent = `
          /* Hide chrome — the mini app provides its own */
          .stage-label, .stage-meta, .stage-bottom, .nav-pane, #tweaks { display:none !important; }
          /* Make the section fill the iframe without phone frame */
          html,body { background:#fff !important; overflow:hidden !important; }
          body { display:block !important; min-height:100% !important; height:100% !important; }
          .phone {
            position:fixed !important; inset:0 !important;
            width:100% !important; height:100% !important;
            border:0 !important; border-radius:0 !important;
            box-shadow:none !important;
            transform:none !important;
          }
          .phone::before { display:none !important; }
          .status-bar { display:none !important; }
          .tg-header { display:none !important; }
          .view { top:0 !important; }
          /* Internal section tabbar — hide; we use the global one */
          .tabbar { display:none !important; }
          .view.has-tabbar { bottom:0 !important; }
        `;
        doc.head.appendChild(css);

        // Listen for "onboarding finished" signal from the inner page
        // (we patch its `finish()` action via postMessage convention)
        const inner = frame.contentWindow;
        if(inner && currentId === 'onboarding'){
          // Override the inner Proto.finish if present
          const tryPatch = () => {
            if(inner.Proto && !inner.__patched){
              inner.__patched = true;
              const origFinish = inner.Proto.finish;
              // The engine wires `actions.finish` via alert; we can intercept via window.alert
              const origAlert = inner.alert;
              inner.alert = function(msg){
                if(String(msg||'').toLowerCase().includes('онбординг')){
                  markOnboarded();
                  if(tg && tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
                  goSection('search');
                  return;
                }
                origAlert.call(inner, msg);
              };
            }
          };
          setTimeout(tryPatch, 100);
          setTimeout(tryPatch, 500);
        }
      }
    } catch(e) { console.warn('chrome strip failed', e); }

    setTimeout(() => splash.classList.add('gone'), 150);
  });

  // ---- Telegram BackButton ----
  // Wire BackButton: tapping = press the in-section back button if available, else close mini app
  if(tg && tg.BackButton){
    tg.BackButton.onClick(() => {
      try {
        const doc = frame.contentDocument;
        const back = doc && doc.querySelector('.s-head .back, [data-act="back"]');
        if(back){ back.click(); return; }
      } catch(e){}
      // Fallback: go to first tab
      if(currentId !== 'search') goSection('search');
      else tg.close();
    });
    // Show on every section except onboarding tab=0
    tg.BackButton.show();
  }

  // ---- Initial section ----
  function initial(){
    const fromHash = location.hash.replace('#','');
    if(fromHash && SECTIONS.find(s => s.id === fromHash)){
      goSection(fromHash);
      return;
    }
    if(!isOnboarded()){
      goSection('onboarding');
    } else {
      goSection('search');
    }
  }
  initial();

  // Listen for hash changes (e.g. external deep link)
  window.addEventListener('hashchange', () => {
    const id = location.hash.replace('#','');
    if(id && SECTIONS.find(s => s.id === id)) goSection(id);
  });

  // Public for debugging
  window.StazhkaApp = { goSection, markOnboarded, sections: SECTIONS };
})();
