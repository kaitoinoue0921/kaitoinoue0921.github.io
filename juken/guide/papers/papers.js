(() => {
  const form = document.querySelector('#paper-form');
  const results = document.querySelector('#saved-papers');
  const filter = document.querySelector('#paper-filter');
  const status = document.querySelector('#paper-status');
  const key = 'juken-saved-papers-v1';

  function safeAddress(text) {
    try {
      const address = new URL(text);
      if (['https:', 'http:'].includes(address.protocol) && !address.username && !address.password) {
        return address.href;
      }
    } catch {
      return null;
    }
    return null;
  }

  function storedPapers() {
    const data = JSON.parse(localStorage.getItem(key) || '[]');
    if (!Array.isArray(data)) return [];
    return data.filter(item => item && typeof item.id === 'string' && typeof item.name === 'string' && safeAddress(item.url));
  }

  function notify(message) {
    status.textContent = message;
  }

  function save(papers) {
    localStorage.setItem(key, JSON.stringify(papers));
  }

  function node(tag, text, className) {
    const item = document.createElement(tag);
    item.textContent = text;
    if (className) item.className = className;
    return item;
  }

  function paperCard(item) {
    const card = node('li', '', 'subject-group');
    const anchor = node('a', item.name, 'text-link');
    anchor.href = safeAddress(item.url);
    const description = node('p', [item.year, item.subject].filter(Boolean).join(' · '), 'muted');
    const remove = node('button', '一覧から削除', 'button');
    remove.type = 'button';
    remove.setAttribute('aria-label', item.name + 'を一覧から削除');
    remove.addEventListener('click', () => {
      try {
        save(storedPapers().filter(paper => paper.id !== item.id));
        render();
        filter.focus();
        notify('一覧から削除しました。');
      } catch {
        notify('削除できませんでした。ブラウザの保存設定を確認してください。');
      }
    });
    card.append(anchor, description);
    if (item.unit) {
      const unit = node('p', 'つまずいた単元　' + item.unit);
      const lesson = node('a', 'この単元の解法を探す', 'text-link');
      const params = new URLSearchParams({q: item.unit, notes: '1'});
      lesson.href = '../?' + params + '#find';
      card.append(unit, lesson);
    }
    card.append(node('div', '', 'paper-actions'));
    card.lastElementChild.append(remove);
    return card;
  }

  function render() {
    const papers = storedPapers();
    const query = filter.value.trim().normalize('NFKC').toLowerCase();
    const shown = papers.filter(item =>
      [item.name, item.year, item.subject, item.unit].join(' ').normalize('NFKC').toLowerCase().includes(query));
    results.replaceChildren(...shown.map(paperCard));
    document.querySelector('#paper-count').textContent = papers.length
      ? shown.length + '件を表示'
      : '保存した過去問はまだありません。';
  }

  form.hidden = false;
  filter.closest('label').hidden = false;
  try {
    render();
  } catch {
    notify('ブラウザ内の保存を読み込めませんでした。');
  }
  filter.addEventListener('input', () => {
    try {
      render();
    } catch {
      notify('ブラウザ内の保存を読み込めませんでした。');
    }
  });
  form.addEventListener('submit', event => {
    event.preventDefault();
    const values = new FormData(form);
    const url = safeAddress(values.get('url').trim());
    const name = values.get('name').trim();
    if (!url || !name) {
      notify('公開ページのURL（https:// または http://）と名前を入力してください。');
      return;
    }
    const year = values.get('year').trim();
    const subject = values.get('subject').trim();
    const unit = values.get('unit').trim();
    const id = JSON.stringify([url, name, year, subject]);
    try {
      const before = storedPapers();
      save([{id, url, name, year, subject, unit}, ...before.filter(item => item.id !== id)]);
      form.reset();
      filter.value = '';
      render();
      notify('このブラウザの一覧に保存しました。');
    } catch {
      notify('保存できませんでした。ブラウザの保存設定を確認してください。');
    }
  });
  addEventListener('storage', event => {
    if (event.key === key) {
      try { render(); } catch { notify('ブラウザ内の保存を読み込めませんでした。'); }
    }
  });
})();
