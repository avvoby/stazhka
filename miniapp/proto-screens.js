/* ============================================================
   Stazhka Onboarding — 5 экранов (welcome → 3 шага формы → summary)
   Каждый экран: { id, render(state, actions), bind?(root, state, actions) }
   Тест по навыкам (Excel/Python/Cases) переехал в Profile → Навыки → «Тест»
   как опциональный.
   ============================================================ */
window.OnboardingScreens = (function(){

  const chev = '<span class="chev">›</span>';
  function esc(s){ return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  const backIcon = '<svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg>';

  /* ---------- Хелперы валидации ---------- */
  function fioParts(v){ return (v || '').trim().split(/\s+/).filter(Boolean); }
  function companiesArr(v){ return (v || '').split(',').map(x => x.trim()).filter(Boolean); }

  /* ---------- O-1: Welcome ---------- */
  const O1 = {
    id: 'O-1', name: 'Приветствие',
    render(s, a){
      return `
      <div class="screen active" data-id="O-1">
        <div class="logo-wrap">
          <div class="logo-mark">С</div>
          <div class="title">Стажка</div>
          <div class="subtitle">За 2 минуты соберу твой профиль и покажу первые вакансии</div>
        </div>
        <button class="btn" data-act="next">Начать</button>
      </div>`;
    }
  };

  /* ---------- O-2: ФИО + курс ---------- */
  const COURSES = ['1 курс', '2 курс', '3 курс', '4 курс', 'Магистратура'];
  const O2 = {
    id: 'O-2', name: 'Имя и курс',
    render(s, a){
      const v = s.fio || '';
      const touched = s._touched && s._touched.fio;
      const fioValid = fioParts(v).length >= 2;
      const fioErr = touched && !fioValid;
      const valid = fioValid && !!s.course;
      return `
      <div class="screen active" data-id="O-2">
        <div class="s-head">
          <button class="back" data-act="back">${backIcon}</button>
          <div class="pill">Шаг 1 из 3</div>
        </div>
        <div class="title">Знакомимся</div>
        <div class="subtitle">ФИО попадёт в твой cover letter, курс — в фильтр подборки</div>

        <input class="input ${fioErr?'err':''}" id="fld-fio"
               placeholder="Имя Фамилия" value="${esc(v)}" autocomplete="off">
        <div class="field-hint ${fioErr?'err':''}">
          ${fioErr ? 'Нужно минимум два слова' : 'Имя и фамилия через пробел'}
        </div>

        <div class="group-title" style="margin-top:18px">На каком ты курсе</div>
        <div class="chip-grid">
          ${COURSES.map(c => `<div class="chip ${s.course === c ? 'active' : ''}" data-course="${c}">${c}</div>`).join('')}
        </div>

        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${valid ? '' : 'aria-disabled="true"'}>Далее</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      const fld = root.querySelector('#fld-fio');
      const hint = root.querySelector('.field-hint');
      const btn = root.querySelector('[data-act="next"]');

      function refreshBtn(){
        const valid = fioParts(s.fio).length >= 2 && !!s.course;
        btn.toggleAttribute('aria-disabled', !valid);
      }
      function refreshFio(){
        const valid = fioParts(s.fio).length >= 2;
        if(s._touched.fio){
          fld.classList.toggle('err', !valid);
          hint.classList.toggle('err', !valid);
          hint.textContent = valid ? 'Имя и фамилия через пробел' : 'Нужно минимум два слова';
        }
      }

      fld.addEventListener('input', e => { s.fio = e.target.value; refreshBtn(); refreshFio(); });
      fld.addEventListener('blur', () => { s._touched.fio = true; refreshFio(); });

      root.querySelectorAll('[data-course]').forEach(el => {
        el.addEventListener('click', () => { s.course = el.dataset.course; a.rerender(); });
      });
    }
  };

  /* ---------- O-3: Программа ---------- */
  const PROGRAMS = [
    'Управление бизнесом',
    'Бизнес-информатика',
    'Маркетинг и рыночная аналитика',
    'Цифровые инновации в управлении',
    'УЦПиБА',
    'Другая ОП'
  ];
  const O3 = {
    id: 'O-3', name: 'Программа',
    render(s, a){
      return `
      <div class="screen active" data-id="O-3">
        <div class="s-head">
          <button class="back" data-act="back">${backIcon}</button>
          <div class="pill">Шаг 2 из 3</div>
        </div>
        <div class="title">Выбери свою программу</div>
        <div class="subtitle">Можно будет изменить позже в профиле</div>
        <div class="rowlist">
          ${PROGRAMS.map(p => `<div class="rowbtn ${s.program === p ? 'active' : ''}" data-program="${p}">${p}${chev}</div>`).join('')}
        </div>
        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${s.program ? '' : 'aria-disabled="true"'}>Далее</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      root.querySelectorAll('[data-program]').forEach(el => {
        el.addEventListener('click', () => { s.program = el.dataset.program; a.rerender(); });
      });
    }
  };

  /* ---------- O-4: Направление + компании мечты ---------- */
  const DIRECTIONS = ['Финансы', 'Консалтинг', 'Маркетинг', 'IT и продукт', 'HR', 'Операции'];
  const O4 = {
    id: 'O-4', name: 'Направление и компании',
    render(s, a){
      const v = s.companies || '';
      const arr = companiesArr(v);
      const over = arr.length > 3;
      const compValid = arr.length >= 1 && !over;
      const valid = !!s.direction && compValid;
      return `
      <div class="screen active" data-id="O-4">
        <div class="s-head">
          <button class="back" data-act="back">${backIcon}</button>
          <div class="pill">Шаг 3 из 3</div>
        </div>
        <div class="title">Что интересно и куда хочется</div>
        <div class="subtitle">Подборка станет точнее, по компаниям пришлём алерт</div>

        <div class="group-title">Направление</div>
        <div class="chip-grid">
          ${DIRECTIONS.map(d => `<div class="chip ${s.direction === d ? 'active' : ''}" data-dir="${d}">${d}</div>`).join('')}
        </div>

        <div class="group-title" style="margin-top:18px">До 3 компаний мечты</div>
        <input class="input ${over ? 'err' : ''}" id="fld-comp"
               placeholder="Сбер, Яков и Партнёры, Авито" value="${esc(v)}" autocomplete="off">
        <div class="field-hint ${over ? 'err' : ''}">
          ${over ? 'Слишком много — оставь не больше 3' : 'Через запятую · указано: ' + arr.length + ' из 3'}
        </div>

        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${valid ? '' : 'aria-disabled="true"'}>Завершить</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      root.querySelectorAll('[data-dir]').forEach(el => {
        el.addEventListener('click', () => { s.direction = el.dataset.dir; a.rerender(); });
      });
      const fld = root.querySelector('#fld-comp');
      const hint = root.querySelector('.field-hint');
      const btn = root.querySelector('[data-act="next"]');
      function refresh(){
        const arr = companiesArr(s.companies);
        const over = arr.length > 3;
        const compValid = arr.length >= 1 && !over;
        const valid = !!s.direction && compValid;
        btn.toggleAttribute('aria-disabled', !valid);
        fld.classList.toggle('err', over);
        hint.classList.toggle('err', over);
        hint.textContent = over ? 'Слишком много — оставь не больше 3' : 'Через запятую · указано: ' + arr.length + ' из 3';
      }
      fld.addEventListener('input', e => { s.companies = e.target.value; refresh(); });
    }
  };

  /* ---------- O-5: Summary ---------- */
  const O5 = {
    id: 'O-5', name: 'Профиль готов',
    render(s, a){
      const companies = companiesArr(s.companies).join(', ');
      return `
      <div class="screen active" data-id="O-5">
        <div class="s-head">
          <button class="back" data-act="back">${backIcon}</button>
          <div class="pill">Готово</div>
        </div>
        <div class="title">Профиль готов</div>
        <div class="subtitle">Проверь данные — можно изменить в профиле</div>
        <div class="summary">
          <div class="name">${esc(s.fio || '—')}</div>
          <div class="sub">${esc(s.course || '—')} · ${esc(s.program || '—')}</div>
          <div class="kv"><span>Направление</span><span>${esc(s.direction || '—')}</span></div>
          <div class="kv"><span>Компании мечты</span><span>${esc(companies || '—')}</span></div>
        </div>
        <div class="spacer"></div>
        <button class="btn" data-act="finish">Перейти к подборке</button>
        <button class="btn ghost" style="margin-top:8px" data-act="reset">Начать заново</button>
      </div>`;
    }
  };

  return [O1, O2, O3, O4, O5];
})();
