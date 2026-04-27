/* ============================================================
   Stazhka onboarding prototype — engine
   Renders current screen, handles actions, persists state.
   ============================================================ */

(function(){
  const Store = window.Store;
  const screens = window.Screens;
  const view = document.getElementById('view');
  const nav  = document.getElementById('nav');
  const trace = document.getElementById('trace');

  // ---------- initial state ----------
  // Транзитное (idx, _touched) — в замыкании. Персистентное (fio, course, …) — из Store.user.
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

  // ---------- render ----------
  const actions = {
    rerender: () => render(),
    next: () => go(state.idx + 1),
    back: () => go(state.idx - 1),
    jump: (i) => go(i),
    finish: () => {
      Store.update({ meta: { onboardingDone: true } });
      alert('Онбординг завершён. В реальном приложении — переход в таб «Поиск» → Подборка');
    },
    reset: () => { Store.reset(); state = buildState(); render(); }
  };

  function go(i){
    i = Math.max(0, Math.min(screens.length-1, i));
    state.idx = i;
    save();
    render();
  }

  function render(){
    const s = screens[state.idx];
    view.innerHTML = s.render(state, actions);
    // wire actions
    view.querySelectorAll('[data-act]').forEach(el=>{
      el.addEventListener('click', ev=>{
        if(el.getAttribute('aria-disabled')==='true') return;
        const a = el.dataset.act;
        if(actions[a]) actions[a]();
      });
    });
    if(s.bind) s.bind(view, state, actions);
    renderNav();
    save();
    trace.textContent = `${s.id} · ${state.idx+1}/${screens.length}`;
  }

  function renderNav(){
    nav.innerHTML = '<div class="label">Экраны</div>' + screens.map((s,i)=>{
      return `<button data-go="${i}" class="${i===state.idx?'on':''}">
        <span class="code">${s.id}</span>
        <span>${s.name}</span>
      </button>`;
    }).join('');
    nav.querySelectorAll('[data-go]').forEach(el=>{
      el.addEventListener('click', ()=> go(parseInt(el.dataset.go,10)));
    });
  }

  // ---------- keyboard ----------
  document.addEventListener('keydown', (e)=>{
    if(e.target.matches('input,textarea,select')) {
      if(e.key === 'Enter'){
        const btn = view.querySelector('[data-act="next"]:not([aria-disabled="true"])');
        if(btn) btn.click();
      }
      return;
    }
    if(e.key === 'ArrowRight') go(state.idx+1);
    else if(e.key === 'ArrowLeft') go(state.idx-1);
    else if(e.key.toLowerCase()==='r') actions.reset();
    else if(e.key.toLowerCase()==='t') window.Proto.toggleTweaks();
  });

  // ---------- Tweaks ----------
  const TW = window.__TWEAKS;
  function applyAccent(c){
    document.documentElement.style.setProperty('--accent', c);
    // lighten for accent-2
    document.documentElement.style.setProperty('--accent-2', hexToTint(c, .92));
  }
  function hexToTint(hex, alpha){
    const r=parseInt(hex.slice(1,3),16), g=parseInt(hex.slice(3,5),16), b=parseInt(hex.slice(5,7),16);
    const mix = (c)=> Math.round(c*(1-alpha) + 255*alpha);
    return `rgb(${mix(r)}, ${mix(g)}, ${mix(b)})`;
  }

  applyAccent(TW.accent);

  // dynamic phone scale
  function fitPhone(){
    const baseW = 390 + 20, baseH = 810 + 40; // phone size + border allowance
    const availW = Math.min(window.innerWidth - 40, 900); // leave room for nav on wide
    const availH = window.innerHeight - 80; // bottom controls
    const s = Math.min(1, availW/baseW, availH/baseH);
    document.documentElement.style.setProperty('--phone-scale', s.toFixed(3));
  }
  fitPhone();
  window.addEventListener('resize', fitPhone);

  // swatches
  document.querySelectorAll('#tweaks .sw').forEach(el=>{
    el.addEventListener('click', ()=>{
      document.querySelectorAll('#tweaks .sw').forEach(x=>x.classList.remove('on'));
      el.classList.add('on');
      const c = el.dataset.c;
      TW.accent = c;
      applyAccent(c);
      persistTweaks();
    });
  });

  // Telegram header toggle
  const twTg = document.getElementById('tw-tg');
  function applyTg(){
    const on = TW.showTelegramHeader;
    document.querySelector('.tg-header').style.display = on ? '' : 'none';
    document.querySelector('.view').style.top = on ? '96px' : '54px';
    twTg.classList.toggle('on', on);
    twTg.textContent = on ? 'вкл' : 'выкл';
  }
  twTg.addEventListener('click', ()=>{
    TW.showTelegramHeader = !TW.showTelegramHeader;
    applyTg();
    persistTweaks();
  });
  applyTg();

  // Jump select
  const twJump = document.getElementById('tw-jump');
  twJump.innerHTML = screens.map((s,i)=>`<option value="${i}">${s.id} · ${s.name}</option>`).join('');
  twJump.value = state.idx;
  twJump.addEventListener('change', e=> go(parseInt(e.target.value,10)));

  // Autofill quiz (dev)
  const twQuiz = document.getElementById('tw-quiz');
  twQuiz.addEventListener('click', ()=>{
    const on = twQuiz.classList.toggle('on');
    twQuiz.textContent = on ? 'вкл' : 'выкл';
    if(on){
      state.q_excel = 0; state.q_excel_correct = true;
      state.q_python = 0; state.q_python_correct = true;
      state.q_cases = 0; state.q_cases_correct = true;
      if(!state.fio) state.fio = 'Иван Иванов';
      if(!state.course) state.course = '3 курс';
      if(!state.program) state.program = 'Бизнес-информатика';
      if(!state.direction) state.direction = 'Консалтинг';
      if(!state.companies) state.companies = 'Сбер, Яков и Партнёры, Авито';
      render();
    }
  });

  function persistTweaks(){
    window.parent.postMessage({type:'__edit_mode_set_keys', edits:{
      accent: TW.accent,
      showTelegramHeader: TW.showTelegramHeader
    }}, '*');
  }

  // ---------- Edit mode contract ----------
  window.addEventListener('message', (e)=>{
    if(!e.data) return;
    if(e.data.type === '__activate_edit_mode') document.getElementById('tweaks').classList.add('on');
    else if(e.data.type === '__deactivate_edit_mode') document.getElementById('tweaks').classList.remove('on');
  });
  window.parent.postMessage({type:'__edit_mode_available'}, '*');

  // ---------- Public API ----------
  window.Proto = {
    reset: actions.reset,
    go,
    toggleTweaks: ()=> document.getElementById('tweaks').classList.toggle('on')
  };

  // rewire jump select on every render (idx changes)
  const origGo = go;
  window.Proto.go = (i)=>{ origGo(i); twJump.value = state.idx; };

  render();
})();
