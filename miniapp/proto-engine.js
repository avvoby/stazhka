/* ============================================================
   Stazhka Onboarding — секция SPA
   Регистрируется в window.SectionRegistry, монтируется по требованию
   ============================================================ */
(function(){
  const Store = window.Store;
  const screens = window.OnboardingScreens;

  // ---------- Состояние ----------
  // Транзитное (idx, _touched) — в замыкании. Персистентное (fio, course, …) — Store.user.
  // companies в Store массив, в state онбординга — строка для текстового ввода.
  function buildState(){
    const u = Store.get().user;
    return {
      idx: 0,
      fio: u.fio || '',
      course: u.course,
      program: u.program,
      q_excel: u.q_excel, q_excel_correct: !!u.q_excel_correct,
      q_python: u.q_python, q_python_correct: !!u.q_python_correct,
      q_cases: u.q_cases, q_cases_correct: !!u.q_cases_correct,
      direction: u.direction,
      companies: Array.isArray(u.companies) ? u.companies.join(', ') : '',
      _touched: { fio: !!u.fio }
    };
  }

  let state = buildState();
  let viewEl = null;

  function save(){
    Store.update({
      user: {
        fio: state.fio,
        course: state.course,
        program: state.program,
        direction: state.direction,
        companies: Store.parseCompanies(state.companies),
        q_excel: state.q_excel,
        q_excel_correct: !!state.q_excel_correct,
        q_python: state.q_python,
        q_python_correct: !!state.q_python_correct,
        q_cases: state.q_cases,
        q_cases_correct: !!state.q_cases_correct
      }
    });
  }

  // ---------- Действия ----------
  const actions = {
    rerender: () => render(),
    next: () => go(state.idx + 1),
    back: () => go(state.idx - 1),
    jump: (i) => go(i),
    finish: () => {
      Store.update({ meta: { onboardingDone: true } });
      if(window.StazhkaApp) window.StazhkaApp.navigate('search');
    },
    reset: () => { Store.reset(); state = buildState(); render(); }
  };

  function go(i){
    i = Math.max(0, Math.min(screens.length - 1, i));
    state.idx = i;
    save();
    render();
  }

  function render(){
    if(!viewEl) return;
    const s = screens[state.idx];
    viewEl.innerHTML = s.render(state, actions);
    viewEl.querySelectorAll('[data-act]').forEach(el => {
      el.addEventListener('click', () => {
        if(el.getAttribute('aria-disabled') === 'true') return;
        const a = el.dataset.act;
        if(actions[a]) actions[a]();
      });
    });
    if(s.bind) s.bind(viewEl, state, actions);
    save();
    if(window.StazhkaApp) window.StazhkaApp.onScreenRendered('onboarding', s.id, viewEl);
  }

  // ---------- Mount/unmount ----------
  function mount(container, _initialScreenId){
    viewEl = container;
    state = buildState();
    render();
  }
  function unmount(){
    if(viewEl) viewEl.innerHTML = '';
    viewEl = null;
  }

  window.SectionRegistry.register('onboarding', { mount, unmount, goTo: (i) => go(parseInt(i, 10) || 0) });
})();
