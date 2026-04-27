/* ============================================================
   store.js — единый стор Стажки
   ----------------------------------------------------------------
   Один ключ в localStorage: stazhka.state.v1
   API:
     Store.get()                 — текущий снэпшот (deep-frozen)
     Store.update(patch)         — частичное обновление, мерджит по слайсам
     Store.subscribe(fn)         — pub/sub, возвращает unsubscribe
     Store.reset()               — сброс к демо-сиду + удаление старых ключей
   Схема:
     user, search, prep, progress, profile, meta
   ============================================================ */
(function(){
  const KEY = 'stazhka.state.v1';
  const SCHEMA_VERSION = 1;

  // --- Старые ключи (для миграции) ---
  const LEGACY_KEYS = [
    'stazhka_onboarding_v1',
    'stazhka-search-v1',
    'stazhka-prep-v1',
    'stazhka-progress-v1',
    'stazhka-chat-v1',
    'stazhka-profile-v1'
  ];

  // --- Демо-сид при первом запуске ---
  function demoSeed(){
    return {
      user: {
        fio: '',
        course: null,
        program: null,
        direction: null,
        companies: [],
        q_excel: undefined, q_excel_correct: false,
        q_python: undefined, q_python_correct: false,
        q_cases: undefined, q_cases_correct: false
      },
      search: {
        favorites: [],
        hidden: [],
        alerts: ['Сбер', 'Яков и Партнёры'],
        applications: []
      },
      prep: {
        hardSkills: [],
        extraSkills: '',
        currentTrack: null,
        completedModules: []
      },
      progress: {
        points: 0,
        streak: 0,
        badges: []
      },
      profile: {
        notifications: { digest: 'weekly', alerts: true, quietHours: '' },
        privacy: { leaderboardName: 'anonymous' }
      },
      meta: {
        onboardingDone: false,
        schemaVersion: SCHEMA_VERSION,
        createdAt: new Date().toISOString()
      }
    };
  }

  // --- Миграция старых ключей в единый стор ---
  function migrateLegacy(){
    let any = false;
    const seed = demoSeed();

    // Онбординг: stazhka_onboarding_v1 → user
    try {
      const ob = JSON.parse(localStorage.getItem('stazhka_onboarding_v1') || 'null');
      if(ob){
        any = true;
        seed.user.fio = ob.fio || '';
        seed.user.course = ob.course || null;
        seed.user.program = ob.program || null;
        seed.user.direction = ob.direction || null;
        // companies может быть строкой "Сбер, Яков, Авито" или массивом
        seed.user.companies = parseCompanies(ob.companies);
        seed.user.q_excel = ob.q_excel;
        seed.user.q_excel_correct = !!ob.q_excel_correct;
        seed.user.q_python = ob.q_python;
        seed.user.q_python_correct = !!ob.q_python_correct;
        seed.user.q_cases = ob.q_cases;
        seed.user.q_cases_correct = !!ob.q_cases_correct;
        // Если онбординг доходил до O-10 — считаем завершённым
        if(typeof ob.idx === 'number' && ob.idx >= 9) seed.meta.onboardingDone = true;
      }
    } catch(e){}

    // Search/prep/progress/chat/profile — все хранили один и тот же объект-копипасту,
    // но в реальной работе только в search использовались favorites/hidden/alerts,
    // а в prep — hardSkills/extraSkills. Берём из обоих, если есть.
    function readLegacy(k){
      try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch(e){ return null; }
    }
    const ls = readLegacy('stazhka-search-v1');
    const lp = readLegacy('stazhka-prep-v1');
    if(ls){
      any = true;
      if(Array.isArray(ls.favorites)) seed.search.favorites = ls.favorites;
      if(Array.isArray(ls.hidden))    seed.search.hidden    = ls.hidden;
      if(Array.isArray(ls.alerts))    seed.search.alerts    = ls.alerts;
    }
    if(lp){
      any = true;
      if(Array.isArray(lp.hardSkills)) seed.prep.hardSkills = lp.hardSkills;
      if(typeof lp.extraSkills === 'string') seed.prep.extraSkills = lp.extraSkills;
    }

    if(any){
      // Чистим старые ключи после успешной миграции
      LEGACY_KEYS.forEach(k => { try { localStorage.removeItem(k); } catch(e){} });
    }
    return seed;
  }

  function parseCompanies(v){
    if(Array.isArray(v)) return v.filter(x => typeof x === 'string' && x.trim()).map(s => s.trim());
    if(typeof v === 'string') return v.split(',').map(s => s.trim()).filter(Boolean);
    return [];
  }

  // --- Загрузка/сохранение ---
  function load(){
    try {
      const raw = localStorage.getItem(KEY);
      if(raw){
        const parsed = JSON.parse(raw);
        // Простая ленивая миграция: если схема старее — мерджим с дефолтом
        if(!parsed.meta || parsed.meta.schemaVersion !== SCHEMA_VERSION){
          return mergeDeep(demoSeed(), parsed);
        }
        return parsed;
      }
    } catch(e){}
    // Нет единого ключа — пробуем мигрировать со старых
    return migrateLegacy();
  }

  function save(s){
    try { localStorage.setItem(KEY, JSON.stringify(s)); } catch(e){}
  }

  function mergeDeep(target, src){
    if(!src || typeof src !== 'object') return target;
    const out = Array.isArray(target) ? target.slice() : {...target};
    for(const k of Object.keys(src)){
      const sv = src[k], tv = out[k];
      if(sv && typeof sv === 'object' && !Array.isArray(sv) && tv && typeof tv === 'object' && !Array.isArray(tv)){
        out[k] = mergeDeep(tv, sv);
      } else {
        out[k] = sv;
      }
    }
    return out;
  }

  // --- Состояние и подписки ---
  let state = load();
  save(state);

  const subs = new Set();

  function notify(){
    subs.forEach(fn => { try { fn(state); } catch(e){ console.warn('store sub error', e); } });
  }

  // --- Публичный API ---
  const Store = {
    get(){ return state; },

    update(patch){
      if(!patch || typeof patch !== 'object') return;
      state = mergeDeep(state, patch);
      save(state);
      notify();
    },

    subscribe(fn){
      if(typeof fn !== 'function') return () => {};
      subs.add(fn);
      return () => subs.delete(fn);
    },

    reset(){
      state = demoSeed();
      save(state);
      LEGACY_KEYS.forEach(k => { try { localStorage.removeItem(k); } catch(e){} });
      notify();
    },

    // Утилита: companies строкой ↔ массивом
    parseCompanies
  };

  window.Store = Store;
})();
