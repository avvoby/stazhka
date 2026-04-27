/* ============================================================
   Search prototype engine — routing, state, tabbar, tweaks, sheet
   ============================================================ */
(function(){

const Store = window.Store;
const TABS = [
  {id:'search',   label:'Поиск',      href:'Stazhka Search.html',   icon:'<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>'},
  {id:'prep',     label:'Подготовка', href:'Stazhka Prep.html',     icon:'<svg viewBox="0 0 24 24"><path d="M4 19.5V6a2 2 0 0 1 2-2h12v16H6a2 2 0 0 0-2 2z"/><path d="M8 8h8M8 12h6"/></svg>'},
  {id:'progress', label:'Прогресс',   href:'Stazhka Progress.html', icon:'<svg viewBox="0 0 24 24"><path d="M4 20V10M10 20V4M16 20v-8M22 20H2"/></svg>'},
  {id:'chat', label:'Чат', href:'Stazhka Chat.html',               icon:'<svg viewBox="0 0 24 24"><path d="M21 15a4 4 0 0 1-4 4H8l-5 3V7a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v8z"/></svg>'},
  {id:'profile', label:'Профиль', href:'Stazhka Profile.html',               icon:'<svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>'}
];

/* ---------- State ---------- */
const defaultState = () => ({
  screenId: 'C-1',
  searchSeg: 'picks',           // picks | manual | fav | alerts
  favorites: [],
  hidden: [],
  alerts: ['Сбер','Яков и Партнёры'],
  manualQuery: '',
  manualPreset: 'Big-3',
  applyingVid: null,
  applyPhase: null,             // null | 'letter' | 'loading' | 'sent'
  letterTone: 'formal',
  hardSkills: [],
  extraSkills: '',
  inviteStage: null,
  rejectStage: null,
  rejectFeedback: '',
  rejectReason: '',
  rejectDiff: ''
});

let state = loadState();
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
    search: {
      favorites: state.favorites,
      hidden: state.hidden,
      alerts: state.alerts
    },
    prep: {
      hardSkills: state.hardSkills,
      extraSkills: state.extraSkills
    }
  });
}

/* ---------- Screens registry ---------- */
const screens = window.Screens;
const byId = Object.fromEntries(screens.map(s=>[s.id, s]));

/* ---------- API ---------- */
const api = {
  rerender(){ render(); },
  goTo(id){
    if(byId[id]){
      state.screenId = id;
      // opening apply as full screen resets phase to letter+loading
      if(id === 'S-7' && !state.applyPhase){
        state.applyPhase = 'loading';
        setTimeout(()=>{ if(state.applyPhase==='loading' && state.screenId==='S-7'){ state.applyPhase='letter'; render(); } }, 1400);
      }
      render();
    }
  },
  openSheet(kind){
    if(kind === 'apply'){
      state.screenId = 'S-7';
      state.applyPhase = 'loading';
      render();
      setTimeout(()=>{ if(state.applyPhase==='loading' && state.screenId==='S-7'){ state.applyPhase='letter'; render(); } }, 1400);
    }
  }
};

/* ---------- Render ---------- */
const viewEl = document.getElementById('view');
const navEl = document.getElementById('nav');
const tabbarEl = document.getElementById('tabbar');
const traceEl = document.getElementById('trace');

/* Nav pane (screen list) */
function renderNav(){
  const html = screens.map(s => `
    <div class="nav-item ${s.id===state.screenId?'active':''}" data-jump="${s.id}">
      <span class="n-id">${s.id}</span>
      <span class="n-label">${s.name}</span>
    </div>
  `).join('');
  navEl.innerHTML = '<div class="label">Экраны</div>' + html;
  navEl.querySelectorAll('[data-jump]').forEach(el=>{
    el.addEventListener('click', ()=> api.goTo(el.dataset.jump));
  });
}

function renderTabbar(){
  tabbarEl.innerHTML = TABS.map(t => `
    <button class="tab ${t.id==='chat'?'active':''} ${t.disabled?'disabled':''}" data-tab="${t.id}">
      ${t.icon}
      <span>${t.label}</span>
    </button>
  `).join('');
  tabbarEl.querySelectorAll('[data-tab]').forEach(btn=>{
    const t = TABS.find(x=>x.id===btn.dataset.tab);
    btn.addEventListener('click', ()=>{
      if(t.disabled){ flashDisabled(btn); return; }
      if(t.id==='chat') return;
      if(t.href) window.location.href = t.href;
    });
  });
}

function flashDisabled(el){
  el.style.transition = 'transform .18s';
  el.style.transform = 'translateY(-2px)';
  setTimeout(()=>{ el.style.transform = ''; }, 180);
}

function render(){
  const screen = byId[state.screenId] || byId['C-1'];
  viewEl.innerHTML = screen.render(state);
  // shared actions
  viewEl.querySelectorAll('[data-go]').forEach(el=>{
    el.addEventListener('click', ()=> api.goTo(el.dataset.go));
  });
  viewEl.querySelectorAll('[data-act="back"]').forEach(el=>{
    el.addEventListener('click', ()=> history.length>1 ? api.goTo('S-1') : null);
  });
  if(screen.bind) screen.bind(viewEl, state, api);

  // nav highlight
  navEl.querySelectorAll('.nav-item').forEach(el=>{
    el.classList.toggle('active', el.dataset.jump === state.screenId);
  });

  // trace
  traceEl.textContent = `${screen.id} · ${screen.name}`;
  saveState();
  applyTweaks();
}

/* ---------- Keyboard ---------- */
document.addEventListener('keydown', (e)=>{
  if(['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) return;
  const idx = screens.findIndex(s=>s.id===state.screenId);
  if(e.key==='ArrowRight' && idx < screens.length-1) api.goTo(screens[idx+1].id);
  else if(e.key==='ArrowLeft' && idx > 0) api.goTo(screens[idx-1].id);
  else if(e.key==='r' || e.key==='R') reset();
  else if(e.key==='t' || e.key==='T') toggleTweaks();
});

/* ---------- Tweaks ---------- */
const tweaksEl = document.getElementById('tweaks');
function toggleTweaks(){ tweaksEl.classList.toggle('open'); }
function applyTweaks(){
  const t = window.__TWEAKS;
  document.documentElement.style.setProperty('--accent', t.accent);
  // accent-2 derived
  const hex = t.accent.replace('#','');
  document.documentElement.style.setProperty('--accent-2', '#'+hex+'14');
  // tg header
  const tg = document.querySelector('.tg-header');
  if(tg) tg.style.display = t.showTelegramHeader ? 'flex' : 'none';
  const statusBar = document.querySelector('.status-bar');
  if(statusBar && !t.showTelegramHeader){
    // no need to reposition; phone layout keeps status bar always
  }
  // tweaks UI state
  document.querySelectorAll('#tweaks .sw').forEach(el=>{
    el.classList.toggle('on', el.dataset.c===t.accent);
  });
  const tgBtn = document.getElementById('tw-tg');
  if(tgBtn){ tgBtn.classList.toggle('on', t.showTelegramHeader); tgBtn.textContent = t.showTelegramHeader?'вкл':'выкл'; }
}

function setTweak(k, v){
  window.__TWEAKS[k] = v;
  try { window.parent.postMessage({type:'__edit_mode_set_keys', edits:{[k]:v}}, '*'); } catch(e){}
  render();
}

document.querySelectorAll('#tweaks .sw').forEach(el=>{
  el.addEventListener('click', ()=> setTweak('accent', el.dataset.c));
});
document.getElementById('tw-tg').addEventListener('click', ()=> setTweak('showTelegramHeader', !window.__TWEAKS.showTelegramHeader));
const jumpSel = document.getElementById('tw-jump');
jumpSel.innerHTML = screens.map(s=>`<option value="${s.id}">${s.id} — ${s.name}</option>`).join('');
jumpSel.value = state.screenId;
jumpSel.addEventListener('change', ()=> api.goTo(jumpSel.value));

/* ---------- Reset ---------- */
function reset(){
  state = defaultState();
  saveState();
  render();
  jumpSel.value = state.screenId;
}

/* ---------- Edit-mode protocol ---------- */
window.addEventListener('message', (e)=>{
  const d = e.data;
  if(!d || typeof d !== 'object') return;
  if(d.type === '__activate_edit_mode') tweaksEl.classList.add('open');
  else if(d.type === '__deactivate_edit_mode') tweaksEl.classList.remove('open');
});
try { window.parent.postMessage({type:'__edit_mode_available'}, '*'); } catch(e){}

/* ---------- Phone scale to viewport ---------- */
function fit(){
  const phone = document.querySelector('.phone');
  if(!phone) return;
  const vh = window.innerHeight;
  const vw = window.innerWidth;
  const baseH = 830;   // phone 810 + a little breathing room
  const baseW = 420;   // phone 390 + margins
  const scale = Math.min(1, vh / baseH, vw / baseW);
  document.documentElement.style.setProperty('--phone-scale', scale);
}
window.addEventListener('resize', fit);
fit();

/* ---------- Expose ---------- */
window.Proto = { reset, toggleTweaks, goTo: api.goTo };

/* ---------- URL hash → starting screen ---------- */
(function(){
  const h = decodeURIComponent(location.hash.replace(/^#/,''));
  if(h && byId[h]) state.screenId = h;
})();

renderNav();
renderTabbar();
render();

})();
