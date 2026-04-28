/* ============================================================
   Stazhka Chat — секция SPA (C-1 ...)
   ============================================================ */
(function(){
  const SECTION_ID = 'chat';
  const DEFAULT_SCREEN = 'C-1';
  const Store = window.Store;
  const screens = window.ChatScreens;
  const byId = Object.fromEntries(screens.map(s => [s.id, s]));

  const defaultState = () => ({
    screenId: DEFAULT_SCREEN,
    searchSeg: 'picks',
    favorites: [],
    hidden: [],
    alerts: [],
    manualQuery: '',
    manualPreset: 'Big-3',
    applyingVid: null,
    applyPhase: null,
    letterTone: 'formal',
    hardSkills: [],
    extraSkills: '',
    inviteStage: null,
    rejectStage: null,
    rejectFeedback: '',
    rejectReason: '',
    rejectDiff: '',
    // Транзитная история активного AI-диалога. На reload теряется (ОК для прототипа).
    chatMessages: [],   // [{role:'user'|'assistant', content, time}]
    chatPending: false,
    chatError: null,
    chatRemaining: null
  });

  function loadState(){
    const s = Store.get();
    return {
      ...defaultState(),
      favorites: s.search.favorites.slice(),
      hidden: s.search.hidden.slice(),
      alerts: s.search.alerts.slice(),
      hardSkills: s.prep.hardSkills.slice(),
      extraSkills: s.prep.extraSkills || ''
    };
  }
  function saveState(){
    Store.update({
      search: { favorites: state.favorites, hidden: state.hidden, alerts: state.alerts },
      prep: { hardSkills: state.hardSkills, extraSkills: state.extraSkills }
    });
  }

  let state = loadState();
  let viewEl = null;

  /* ---------- AI chat client ---------- */
  function fmtTime(d){
    return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }

  async function sendChatMessage(text){
    const trimmed = (text || '').trim();
    if(!trimmed || state.chatPending) return;

    state.chatMessages.push({ role: 'user', content: trimmed, time: fmtTime(new Date()) });
    state.chatPending = true;
    state.chatError = null;
    render();

    const cfg = window.STAZHKA_CONFIG || {};
    const apiBase = (cfg.apiUrl || '').replace(/\/$/, '');
    if(!apiBase){
      state.chatPending = false;
      state.chatError = 'API не настроен. Открой index.html → window.STAZHKA_CONFIG.apiUrl и впиши URL туннеля.';
      render();
      return;
    }

    const u = Store.get().user;
    const tg = window.Telegram && window.Telegram.WebApp;
    const tgUserId = (tg && tg.initDataUnsafe && tg.initDataUnsafe.user && tg.initDataUnsafe.user.id) || 0;

    const payload = {
      tg_user_id: tgUserId,
      messages: state.chatMessages.map(m => ({ role: m.role, content: m.content })),
      profile: {
        fio: u.fio || '',
        course: u.course || null,
        program: u.program || null,
        direction: u.direction || null,
        companies: Array.isArray(u.companies) ? u.companies : []
      }
    };

    try {
      const resp = await fetch(apiBase + '/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Чтобы ngrok не возвращал страницу-предупреждение в API-запросах
          'ngrok-skip-browser-warning': 'true'
        },
        body: JSON.stringify(payload)
      });
      if(!resp.ok){
        let detail = await resp.text();
        try { detail = (JSON.parse(detail).detail) || detail; } catch(_){}
        throw new Error(detail || ('HTTP ' + resp.status));
      }
      const data = await resp.json();
      state.chatMessages.push({ role: 'assistant', content: data.text || '', time: fmtTime(new Date()) });
      state.chatRemaining = typeof data.remaining === 'number' ? data.remaining : null;
    } catch(e){
      state.chatError = String((e && e.message) || e);
    } finally {
      state.chatPending = false;
      render();
    }
  }

  function clearChat(){
    state.chatMessages = [];
    state.chatError = null;
    state.chatRemaining = null;
    render();
  }

  const api = {
    rerender(){ render(); },
    goTo(id){
      if(byId[id]){
        state.screenId = id;
        syncHash();
        render();
      }
    },
    openSheet(){},
    sendChatMessage,
    clearChat
  };

  function syncHash(){
    const target = '#' + SECTION_ID + '/' + state.screenId;
    if(location.hash !== target) history.replaceState(null, '', target);
  }

  function render(){
    if(!viewEl) return;
    const screen = byId[state.screenId] || byId[DEFAULT_SCREEN];
    viewEl.innerHTML = screen.render(state);
    viewEl.querySelectorAll('[data-go]').forEach(el => {
      el.addEventListener('click', () => api.goTo(el.dataset.go));
    });
    viewEl.querySelectorAll('[data-act="back"]').forEach(el => {
      el.addEventListener('click', () => api.goTo(DEFAULT_SCREEN));
    });
    if(screen.bind) screen.bind(viewEl, state, api);
    saveState();
    if(window.StazhkaApp) window.StazhkaApp.onScreenRendered(SECTION_ID, state.screenId, viewEl);
  }

  function mount(container, initialScreenId){
    viewEl = container;
    if(initialScreenId && byId[initialScreenId]){
      state.screenId = initialScreenId;
    } else if(!byId[state.screenId]){
      state.screenId = DEFAULT_SCREEN;
    }
    const fresh = loadState();
    state.favorites = fresh.favorites;
    state.hidden = fresh.hidden;
    state.alerts = fresh.alerts;
    state.hardSkills = fresh.hardSkills;
    state.extraSkills = fresh.extraSkills;
    render();
  }
  function unmount(){
    if(viewEl) viewEl.innerHTML = '';
    viewEl = null;
  }

  window.SectionRegistry.register(SECTION_ID, { mount, unmount, goTo: api.goTo });
})();
