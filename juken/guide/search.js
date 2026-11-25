(() => {
  const form = document.querySelector('#guide-search');
  if (!form) return;
  const result = document.querySelector('#guide-results');
  const count = document.querySelector('#result-status');
  const list = document.querySelector('#result-list');
  const more = document.querySelector('#result-more');
  const fields = form.elements;
  const selectNames = ['subject', 'skill', 'level'];
  const pageSize = 12;
  const sources = new Map();
  let matches = [];
  let displayed = 0;
  let latest = 0;

  function normalize(value) {
    return (value ?? '').normalize('NFKC').toLowerCase().replace(/[ァ-ヶ]/g,
      character => String.fromCharCode(character.charCodeAt(0) - 0x60));
  }

  function load(url) {
    if (!sources.has(url)) {
      sources.set(url, fetch(url).then(response => {
        if (!response.ok) throw Error(response.status);
        return response.json();
      }).catch(error => {
        sources.delete(url);
        throw error;
      }));
    }
    return sources.get(url);
  }

  function makeRow(item) {
    const row = document.createElement('li');
    const anchor = document.createElement('a');
    anchor.href = item.href;
    const detail = document.createElement('small');
    detail.textContent = [item.subjectLabel, item.unit, item.levelLabel].filter(Boolean).join(' · ');
    const title = document.createElement('strong');
    title.textContent = item.title;
    anchor.append(detail, title);
    if (item.cue) {
      const cue = document.createElement('span');
      cue.textContent = item.cue;
      anchor.append(cue);
    }
    row.append(anchor);
    return row;
  }

  function next() {
    const page = matches.slice(displayed, displayed + pageSize);
    list.append(...page.map(makeRow));
    displayed += page.length;
    more.hidden = displayed >= matches.length;
    count.textContent = matches.length
      ? matches.length + '件中 ' + displayed + '件を表示'
      : '一致する解法がありません。条件を減らすか、科目一覧から探してください。';
  }

  function readURL() {
    const params = new URLSearchParams(location.search);
    fields.q.value = params.get('q') ?? '';
    for (const name of selectNames) {
      const value = params.get(name) ?? '';
      fields[name].value = Array.from(fields[name].options).some(option => option.value === value) ? value : '';
    }
    fields.notes.checked = params.get('notes') === '1';
  }

  async function search(updateURL) {
    const current = ++latest;
    const q = fields.q.value.trim();
    const terms = normalize(q).split(/\s+/).filter(Boolean);
    const subject = fields.subject.value;
    const skill = fields.skill.value;
    const level = fields.level.value;
    const useNotes = fields.notes.checked && !skill && !level;
    result.hidden = false;
    count.textContent = '検索中';
    list.replaceChildren();
    more.hidden = true;
    if (updateURL) {
      const params = new URLSearchParams();
      if (q) params.set('q', q);
      for (const name of selectNames) {
        if (fields[name].value) params.set(name, fields[name].value);
      }
      if (fields.notes.checked) params.set('notes', '1');
      const encoded = String(params);
      history.replaceState(null, '', location.pathname + (encoded ? '?' + encoded : '') + '#find');
    }
    try {
      const lessons = await load('search-index.json');
      let merged = lessons;
      let missingNotes = false;
      if (useNotes) {
        try {
          merged = lessons.concat(await load('notes-index.json'));
        } catch {
          missingNotes = true;
        }
      }
      if (current !== latest) return;
      matches = merged.filter(item => {
        if (subject && item.subject !== subject) return false;
        if (skill && item.skill !== skill) return false;
        if (level && item.level !== level) return false;
        const haystack = normalize([item.title, item.unit, item.cue, item.terms, item.subjectLabel, item.skillLabel].join(' '));
        return terms.every(term => haystack.includes(term));
      }).sort((left, right) => {
        const score = item => terms.filter(term => normalize(item.title).includes(term)).length * 4 + (item.note ? 0 : 2);
        return score(right) - score(left);
      });
      displayed = 0;
      next();
      if (missingNotes) count.textContent += '。既存ノートの索引を読み込めませんでした。';
      if (fields.notes.checked && !useNotes) count.textContent += '。既存ノートを検索するには難度と考え方の指定を外してください。';
    } catch {
      if (current === latest) count.textContent = '索引を読み込めませんでした。再検索するか、科目一覧を開いてください。';
    }
  }

  form.hidden = false;
  readURL();
  if (location.search) search(false);
  form.addEventListener('submit', event => {
    event.preventDefault();
    search(true);
  });
  more.addEventListener('click', next);
  addEventListener('popstate', () => {
    readURL();
    if (location.search) search(false);
    else {
      latest++;
      result.hidden = true;
    }
  });
})();
