/* ============================================================
   Stazhka onboarding prototype — screen definitions
   Each screen: { id, render(state, actions) -> HTML }
   ============================================================ */

window.OnboardingScreens = (function(){

  const chev = '<span class="chev">›</span>';

  // ---------- O-1: Welcome
  const O1 = {
    id:'O-1', name:'Приветствие',
    render(s, a){
      return `
      <div class="screen active" data-id="O-1">
        <div class="logo-wrap">
          <div class="logo-mark">С</div>
          <div class="title">Стажка</div>
          <div class="subtitle">За 5 минут соберу твой профиль и покажу первые вакансии</div>
        </div>
        <button class="btn" data-act="next">Начать</button>
      </div>`;
    }
  };

  // ---------- O-2: FIO
  const O2 = {
    id:'O-2', name:'ФИО',
    render(s, a){
      const v = s.fio || '';
      const touched = s._touched.fio;
      const parts = v.trim().split(/\s+/).filter(Boolean);
      const valid = parts.length >= 2;
      const err = touched && !valid;
      return `
      <div class="screen active" data-id="O-2">
        <div class="s-head">
          <button class="back" data-act="back"><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
          <div class="pill">Шаг 1 из 9</div>
        </div>
        <div class="title">Как тебя зовут?</div>
        <div class="subtitle">Укажи полное имя — попадёт в твой cover letter</div>
        <input class="input ${err?'err':''}" id="fld-fio" placeholder="Имя Фамилия" value="${esc(v)}" autocomplete="off">
        <div class="field-hint ${err?'err':''}">${err?'Нужно минимум два слова':'Можно указать фамилию и имя через пробел'}</div>
        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${valid?'':'aria-disabled="true"'}>Далее</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      const fld = root.querySelector('#fld-fio');
      const btn = root.querySelector('[data-act="next"]');
      const hint = root.querySelector('.field-hint');
      function check(){
        const parts = (s.fio||'').trim().split(/\s+/).filter(Boolean);
        const valid = parts.length >= 2;
        if(valid) btn.removeAttribute('aria-disabled');
        else btn.setAttribute('aria-disabled','true');
        if(s._touched.fio){
          fld.classList.toggle('err', !valid);
          hint.classList.toggle('err', !valid);
          hint.textContent = valid ? 'Можно указать фамилию и имя через пробел' : 'Нужно минимум два слова';
        }
      }
      fld.addEventListener('input', e=>{ s.fio = e.target.value; check(); });
      fld.addEventListener('blur', ()=>{ s._touched.fio = true; check(); });
      fld.focus();
      fld.setSelectionRange(fld.value.length, fld.value.length);
    }
  };

  // ---------- O-3: Course
  const COURSES = ['1 курс','2 курс','3 курс','4 курс','Магистратура'];
  const O3 = {
    id:'O-3', name:'Курс',
    render(s){
      return `
      <div class="screen active" data-id="O-3">
        <div class="s-head">
          <button class="back" data-act="back"><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
          <div class="pill">Шаг 2 из 9</div>
        </div>
        <div class="title">На каком ты курсе?</div>
        <div class="subtitle">Учтём это при подборе — не все стажировки берут с 1-2 курса</div>
        <div class="chip-grid">
          ${COURSES.map(c=>`<div class="chip ${s.course===c?'active':''}" data-course="${c}">${c}</div>`).join('')}
        </div>
        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${s.course?'':'aria-disabled="true"'}>Далее</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      root.querySelectorAll('[data-course]').forEach(el=>{
        el.addEventListener('click', ()=>{ s.course = el.dataset.course; a.rerender(); });
      });
    }
  };

  // ---------- O-4: Program
  const PROGRAMS = [
    'Управление бизнесом',
    'Бизнес-информатика',
    'Маркетинг и рыночная аналитика',
    'Цифровые инновации в управлении',
    'УЦПиБА',
    'Другая ОП'
  ];
  const O4 = {
    id:'O-4', name:'Программа',
    render(s){
      return `
      <div class="screen active" data-id="O-4">
        <div class="s-head">
          <button class="back" data-act="back"><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
          <div class="pill">Шаг 3 из 9</div>
        </div>
        <div class="title">Выбери свою программу</div>
        <div class="subtitle">Можно будет изменить позже в профиле</div>
        <div class="rowlist">
          ${PROGRAMS.map(p=>`<div class="rowbtn ${s.program===p?'active':''}" data-program="${p}">${p}${chev}</div>`).join('')}
        </div>
        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${s.program?'':'aria-disabled="true"'}>Далее</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      root.querySelectorAll('[data-program]').forEach(el=>{
        el.addEventListener('click', ()=>{ s.program = el.dataset.program; a.rerender(); });
      });
    }
  };

  // ---------- Skills quiz factory
  function quizScreen(code, stepIdx, kicker, question, answers, correctIdx, progress, stateKey){
    return {
      id: code, name: `Навыки ${stepIdx}/3`,
      render(s){
        const ans = s[stateKey];
        const answered = ans !== undefined;
        return `
        <div class="screen active" data-id="${code}">
          <div class="progress"><span style="width:${progress}%"></span></div>
          <div class="s-head">
            <button class="back" data-act="back"><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
            <div class="pill">${kicker}</div>
          </div>
          <div class="title">${question}</div>
          <div class="subtitle">Ответ повлияет на рекомендации — отвечай честно</div>
          <div class="rowlist">
            ${answers.map((t,i)=>{
              let cls = 'rowbtn';
              if(answered){
                if(i===correctIdx) cls+=' correct';
                else if(i===ans) cls+=' wrong';
                else cls+=' dim';
              }
              return `<div class="${cls}" data-ans="${i}">${t}</div>`;
            }).join('')}
          </div>
          <div class="spacer"></div>
          <div class="btn-row">
            <button class="btn ghost" data-act="back">Назад</button>
            <button class="btn" data-act="next" ${answered?'':'aria-disabled="true"'}>Далее</button>
          </div>
        </div>`;
      },
      bind(root, s, a){
        root.querySelectorAll('[data-ans]').forEach(el=>{
          el.addEventListener('click', ()=>{
            if(s[stateKey] !== undefined) return;
            s[stateKey] = parseInt(el.dataset.ans,10);
            s[stateKey+'_correct'] = (s[stateKey]===correctIdx);
            a.rerender();
          });
        });
      }
    };
  }

  const O5 = quizScreen('O-5', 1, 'Excel · 1 из 3',
    'Что вернёт VLOOKUP, если значение не найдено?',
    ['#N/A','0','Пустая ячейка','Не знаю'],
    0, 33, 'q_excel');

  const O6 = quizScreen('O-6', 2, 'Python · 2 из 3',
    'Что делает df.groupby(\'x\').mean() в pandas?',
    ['Среднее по группам','Сортировку','Фильтр','Не знаю'],
    0, 66, 'q_python');

  const O7 = quizScreen('O-7', 3, 'Кейсы · 3 из 3',
    'Что означает MECE в кейс-интервью?',
    ['Взаимоисключающее и исчерпывающее','Метод оценки рынка','Тип графика','Не знаю'],
    0, 100, 'q_cases');

  // ---------- O-8: Direction
  const DIRECTIONS = ['Финансы','Консалтинг','Маркетинг','IT и продукт','HR','Операции'];
  const O8 = {
    id:'O-8', name:'Направление',
    render(s){
      return `
      <div class="screen active" data-id="O-8">
        <div class="s-head">
          <button class="back" data-act="back"><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
          <div class="pill">Шаг 7 из 9</div>
        </div>
        <div class="title">Какое направление тебе интересно?</div>
        <div class="subtitle">Выбери одно — подборка станет точнее</div>
        <div class="chip-grid">
          ${DIRECTIONS.map(d=>`<div class="chip ${s.direction===d?'active':''}" data-dir="${d}">${d}</div>`).join('')}
        </div>
        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${s.direction?'':'aria-disabled="true"'}>Далее</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      root.querySelectorAll('[data-dir]').forEach(el=>{
        el.addEventListener('click', ()=>{ s.direction = el.dataset.dir; a.rerender(); });
      });
    }
  };

  // ---------- O-9: Dream companies
  const O9 = {
    id:'O-9', name:'Компании мечты',
    render(s){
      const v = s.companies || '';
      const arr = v.split(',').map(x=>x.trim()).filter(Boolean);
      const count = arr.length;
      const over = count > 3;
      const valid = count >= 1 && !over;
      return `
      <div class="screen active" data-id="O-9">
        <div class="s-head">
          <button class="back" data-act="back"><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
          <div class="pill">Шаг 8 из 9</div>
        </div>
        <div class="title">Назови до 3 компаний мечты</div>
        <div class="subtitle">Пришлём алерт, когда у них откроется стажировка</div>
        <input class="input ${over?'err':''}" id="fld-comp" placeholder="Сбер, Яков и Партнёры, Авито" value="${esc(v)}" autocomplete="off">
        <div class="field-hint ${over?'err':''}">
          ${over ? 'Слишком много — оставь не больше 3' : 'Через запятую · указано: ' + count + ' из 3'}
        </div>
        <div class="spacer"></div>
        <div class="btn-row">
          <button class="btn ghost" data-act="back">Назад</button>
          <button class="btn" data-act="next" ${valid?'':'aria-disabled="true"'}>Завершить</button>
        </div>
      </div>`;
    },
    bind(root, s, a){
      const fld = root.querySelector('#fld-comp');
      const btn = root.querySelector('[data-act="next"]');
      const hint = root.querySelector('.field-hint');
      function check(){
        const arr = (s.companies||'').split(',').map(x=>x.trim()).filter(Boolean);
        const over = arr.length > 3;
        const valid = arr.length >= 1 && !over;
        if(valid) btn.removeAttribute('aria-disabled');
        else btn.setAttribute('aria-disabled','true');
        fld.classList.toggle('err', over);
        hint.classList.toggle('err', over);
        hint.textContent = over ? 'Слишком много — оставь не больше 3' : 'Через запятую · указано: ' + arr.length + ' из 3';
      }
      fld.addEventListener('input', e=>{ s.companies = e.target.value; check(); });
      fld.focus();
      fld.setSelectionRange(fld.value.length, fld.value.length);
    }
  };

  // ---------- O-10: Summary
  const O10 = {
    id:'O-10', name:'Профиль готов',
    render(s){
      const companies = (s.companies||'').split(',').map(x=>x.trim()).filter(Boolean).join(', ');
      const excel = s.q_excel_correct ? 'ok' : 'no';
      const py    = s.q_python_correct ? 'ok' : 'no';
      const cases = s.q_cases_correct ? 'ok' : 'no';
      return `
      <div class="screen active" data-id="O-10">
        <div class="s-head">
          <button class="back" data-act="back"><svg viewBox="0 0 24 24"><path d="m15 6-6 6 6 6"/></svg></button>
          <div class="pill">Готово</div>
        </div>
        <div class="title">Профиль готов</div>
        <div class="subtitle">Проверь данные — можно будет изменить в профиле</div>
        <div class="summary">
          <div class="name">${esc(s.fio||'—')}</div>
          <div class="sub">${esc(s.course||'—')} · ${esc(s.program||'—')}</div>
          <div class="kv"><span>Направление</span><span>${esc(s.direction||'—')}</span></div>
          <div class="kv"><span>Навыки</span>
            <span class="skills">
              <span class="sk ${excel}">Excel ${s.q_excel_correct?'1/1':'0/1'}</span>
              <span class="sk ${py}">Python ${s.q_python_correct?'1/1':'0/1'}</span>
              <span class="sk ${cases}">Кейсы ${s.q_cases_correct?'1/1':'0/1'}</span>
            </span>
          </div>
          <div class="kv"><span>Компании мечты</span><span>${esc(companies||'—')}</span></div>
        </div>
        <div class="spacer"></div>
        <button class="btn" data-act="finish">Перейти к подборке</button>
        <button class="btn ghost" style="margin-top:8px" data-act="reset">Начать заново</button>
      </div>`;
    }
  };

  function esc(s){ return String(s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

  return [O1, O2, O3, O4, O5, O6, O7, O8, O9, O10];
})();
