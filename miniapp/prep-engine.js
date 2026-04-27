/* ============================================================
   Stazhka Prep — секция SPA (P-1 ... P-10b)
   ============================================================ */
(function(){
  const SECTION_ID = 'prep';
  const DEFAULT_SCREEN = 'P-1';
  const Store = window.Store;
  const screens = window.PrepScreens;
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
    rejectDiff: ''
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

  const api = {
    rerender(){ render(); },
    goTo(id){
      if(byId[id]){
        state.screenId = id;
        syncHash();
        render();
      }
    },
    openSheet(){}
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
