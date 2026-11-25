(function () {
  'use strict';

  const printButton = document.querySelector('[data-lesson-print]');
  if (printButton) {
    printButton.hidden = false;
    printButton.addEventListener('click', () => window.print());
  }
  const prefix = 'juken-guide:review:v1:';
  const changed = 'guide-review-changed';
  const intervals = [1, 3, 7, 14, 30];
  const storageError = 'このブラウザに保存できませんでした。必要な内容を紙に控えてください。';
  let activeTimer;

  function day(offset = 0, date = new Date()) {
    const local = new Date(date);
    local.setDate(local.getDate() + offset);
    const month = String(local.getMonth() + 1).padStart(2, '0');
    const dateOfMonth = String(local.getDate()).padStart(2, '0');
    return `${local.getFullYear()}-${month}-${dateOfMonth}`;
  }

  function dateLabel(value) {
    const [year, month, date] = value.split('-').map(Number);
    const currentYear = new Date().getFullYear();
    return `${year === currentYear ? '' : `${year}年`}${month}月${date}日`;
  }

  function validDate(value) {
    return typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value);
  }

  function parseRecord(raw, id) {
    try {
      const record = JSON.parse(raw);
      return record && record.id === id && typeof record.title === 'string' ? record : null;
    } catch {
      return null;
    }
  }

  function read(id) {
    return parseRecord(localStorage.getItem(prefix + id), id) || {};
  }

  function write(id, record) {
    if (record.due || record.memo || record.result === 'retry') {
      localStorage.setItem(prefix + id, JSON.stringify(record));
    } else {
      localStorage.removeItem(prefix + id);
    }
    window.dispatchEvent(new CustomEvent(changed, { detail: id }));
  }

  function watch(id, update) {
    window.addEventListener(changed, event => {
      if (!id || event.detail === id) update();
    });
    window.addEventListener('storage', event => {
      if (!event.key || (id ? event.key === prefix + id : event.key.startsWith(prefix))) update();
    });
  }

  function button(label, run, className = 'practice-button') {
    const control = document.createElement('button');
    control.type = 'button';
    control.className = className;
    control.textContent = label;
    control.addEventListener('click', run);
    return control;
  }

  function initTimer(panel) {
    const time = panel.querySelector('[data-timer]');
    const timerStatus = panel.querySelector('[data-timer-status]');
    const toggle = panel.querySelector('[data-timer-toggle]');
    const reset = panel.querySelector('[data-timer-reset]');
    let elapsed = 0;
    let start = null;
    let tick;

    function render() {
      const running = start === null ? 0 : performance.now() - start;
      const seconds = Math.floor((elapsed + running) / 1000);
      time.textContent = `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
    }

    function pause() {
      if (start === null) return;
      elapsed += performance.now() - start;
      start = null;
      clearInterval(tick);
      activeTimer = undefined;
      toggle.textContent = '計時を再開';
      render();
      timerStatus.textContent = `一時停止しました。経過 ${time.textContent}`;
    }

    toggle.addEventListener('click', () => {
      if (start !== null) {
        pause();
        return;
      }
      if (activeTimer) activeTimer();
      activeTimer = pause;
      start = performance.now();
      tick = setInterval(render, 250);
      toggle.textContent = '一時停止';
      reset.disabled = false;
      timerStatus.textContent = '計時中';
      render();
    });

    reset.addEventListener('click', () => {
      pause();
      elapsed = 0;
      toggle.textContent = '計時を開始';
      render();
      toggle.focus();
      reset.disabled = true;
      timerStatus.textContent = '計時をリセットしました。';
    });
  }

  function initPrompt(panel, lesson) {
    const question = lesson.querySelector('[data-problem]');
    if (!question) return;
    const prompt = panel.querySelector('[data-grading-prompt]');
    const answer = lesson.querySelector('[data-answer]');
    const answerText = answer && answer.textContent.trim();
    const output = panel.querySelector('[data-prompt-text]');
    const status = panel.querySelector('[data-prompt-status]');
    output.value = [
      '大学受験の例題に対する、写真の手書き答案を採点してください。',
      '',
      '【問題】',
      question.textContent.trim(),
      ...(answerText ? ['', '【照合用の解答】', answerText] : []),
      '',
      '1. 写真から読める答えと考え方を書き出してください。読めない箇所は推測せず、どこが読めないか示してください。',
      '2. 問題の条件、立てた式や使った根拠、計算や記述、最終答案を確認し、判定を「正解・一部正解・要再考・判定保留」で示してください。別解も妥当なら認めてください。',
      '3. 最初に直すべき箇所を一つ、理由とともに示してください。次に紙で試す一手も一つ書いてください。',
      '4. 最後に、保存用として「判定／できたこと／次の一手」を3行にまとめてください。'
    ].join('\n');
    prompt.hidden = false;
    panel.querySelector('[data-copy-prompt]').addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(output.value);
        status.textContent = '採点用の文をコピーしました。';
      } catch {
        output.focus();
        output.select();
        status.textContent = '文を選択しました。端末のコピー操作を使ってください。';
      }
    });
  }

  function initLesson(lesson) {
    const mount = lesson.querySelector('[data-practice]');
    const heading = lesson.querySelector('h1, h2');
    if (!mount || !heading || !lesson.id) return;

    const id = lesson.id;
    const identity = {
      id,
      title: heading.textContent.trim(),
      subject: lesson.dataset.subjectLabel || '',
      unit: lesson.dataset.unit || '',
      anchor: lesson.dataset.reviewAnchor || ''
    };
    mount.innerHTML = `
      <details class="practice-panel">
        <summary>紙で解く・復習する</summary>
        <div class="practice-panel-body">
          <section class="practice-section" aria-label="時間を測る">
            <p class="practice-label">時間を測る <span class="practice-muted">任意</span></p>
            <div class="practice-actions">
              <output class="practice-time" aria-label="経過時間" aria-live="off" data-timer>0:00</output>
              <button class="practice-button" type="button" data-timer-toggle>計時を開始</button>
              <button class="practice-button" type="button" data-timer-reset disabled>リセット</button>
            </div>
            <p class="practice-sr-only" role="status" data-timer-status></p>
          </section>
          <section class="practice-section" aria-label="復習の予定">
            <p class="practice-label">復習の予定</p>
            <p class="practice-current" data-current-review></p>
            <div class="practice-actions">
              <button class="practice-button" type="button" data-queue>復習に追加</button>
              <button class="practice-button" type="button" data-recall>思い出せた</button>
              <button class="practice-button" type="button" data-retry>詰まった</button>
            </div>
            <p class="practice-muted">紙で解き直してから、思い出せたかを記録します。</p>
            <p class="practice-status" role="status" data-review-status></p>
          </section>
          <details class="practice-section practice-grading">
            <summary>採点の補助とメモ</summary>
            <div data-grading-prompt hidden>
              <p class="practice-muted">手書き答案の氏名・学校名などを隠し、自分のChatGPTなどに写真と下の文を添えます。判定は教材の解答でも確かめましょう。</p>
              <label class="practice-label">AIに渡す採点用の文
                <textarea readonly rows="4" data-prompt-text></textarea>
              </label>
              <div class="practice-actions">
                <button class="practice-button" type="button" data-copy-prompt>採点用の文をコピー</button>
              </div>
              <p class="practice-status" role="status" data-prompt-status></p>
            </div>
            <label class="practice-label">採点メモ
              <textarea rows="3" maxlength="6000" placeholder="できたこと、次に直すこと。AI採点の要点も貼れます。" data-grading-note></textarea>
            </label>
            <div class="practice-actions">
              <button class="practice-button practice-button-primary" type="button" data-save-note>この端末に保存</button>
              <button class="practice-button" type="button" data-delete-note disabled>メモを削除</button>
            </div>
            <p class="practice-muted">メモはこのブラウザに保存されます。共用端末では学習後に削除してください。</p>
            <p class="practice-status" role="status" data-note-status></p>
          </details>
        </div>
      </details>`;
    mount.hidden = false;
    initTimer(mount);
    initPrompt(mount, lesson);

    const current = mount.querySelector('[data-current-review]');
    const reviewStatus = mount.querySelector('[data-review-status]');
    const noteStatus = mount.querySelector('[data-note-status]');
    const note = mount.querySelector('[data-grading-note]');
    const deleteNote = mount.querySelector('[data-delete-note]');
    const queue = mount.querySelector('[data-queue]');
    let lastSavedNote = '';

    function refresh() {
      try {
        const record = read(id);
        const savedNote = typeof record.memo === 'string' ? record.memo : '';
        if (note.value === lastSavedNote) note.value = savedNote;
        lastSavedNote = savedNote;
        deleteNote.disabled = !savedNote;
        const due = validDate(record.due) ? record.due : '';
        current.textContent = due ? `次の復習日 ${dateLabel(due)}` : '復習の予定はまだありません。';
        queue.setAttribute('aria-disabled', String(Boolean(due)));
        queue.textContent = due ? '復習に追加済み' : '復習に追加';
      } catch {
        current.textContent = storageError;
      }
    }

    function updateReview(action) {
      const today = day();
      try {
        const record = { ...read(id), ...identity };
        if (action === 'queue') {
          if (record.due) return;
          record.stage = -1;
          record.due = today;
        } else if (action === 'retry') {
          record.stage = -1;
          record.result = 'retry';
          record.due = day(1);
        } else {
          const stage = Number.isInteger(record.stage) ? record.stage : -1;
          record.result = 'recall';
          if (stage >= 0 && validDate(record.due) && record.due > today) {
            write(id, record);
            reviewStatus.textContent = `現在の復習日 ${dateLabel(record.due)} を残しました。`;
            return;
          }
          record.stage = Math.min(Math.max(stage + 1, 0), intervals.length - 1);
          record.due = day(intervals[record.stage]);
        }
        write(id, record);
        reviewStatus.textContent = `復習を ${dateLabel(record.due)} に設定しました。`;
      } catch {
        reviewStatus.textContent = storageError;
      }
    }

    queue.addEventListener('click', () => updateReview('queue'));
    mount.querySelector('[data-recall]').addEventListener('click', () => updateReview('recall'));
    mount.querySelector('[data-retry]').addEventListener('click', () => updateReview('retry'));
    mount.querySelector('[data-save-note]').addEventListener('click', () => {
      const value = note.value.trim();
      if (!value) {
        noteStatus.textContent = '保存する内容を入力してください。空にしたい場合は「メモを削除」を使えます。';
        return;
      }
      try {
        write(id, { ...read(id), ...identity, memo: value });
        note.value = value;
        lastSavedNote = value;
        noteStatus.textContent = '採点メモを保存しました。';
      } catch {
        noteStatus.textContent = storageError;
      }
    });
    deleteNote.addEventListener('click', () => {
      try {
        const record = read(id);
        delete record.memo;
        write(id, record);
        note.value = '';
        lastSavedNote = '';
        note.focus();
        noteStatus.textContent = '採点メモを削除しました。';
      } catch {
        noteStatus.textContent = storageError;
      }
    });
    refresh();
    watch(id, refresh);
  }

  function reviewHref(record) {
    if (document.getElementById(record.id)?.matches('article.lesson')) {
      return '#' + encodeURIComponent(record.id);
    }
    if (location.protocol !== 'file:' && typeof record.anchor === 'string'
        && /^\/juken\/guide\/[a-z0-9-]+\/(?:[a-z0-9-]+\/|#[a-z0-9-]+)$/.test(record.anchor)) {
      return record.anchor;
    }
    return '/juken/guide/';
  }

  function initReview(mount) {
    const status = document.createElement('p');
    status.className = 'practice-status';
    status.setAttribute('role', 'status');
    const view = document.createElement('div');
    view.className = 'practice-review-groups';
    mount.append(status, view);

    function remove(record, key) {
      try {
        const current = read(record.id);
        delete current[key];
        if (key === 'due') delete current.stage;
        write(record.id, current);
        mount.focus({ preventScroll: true });
        const messages = { due: '復習の予定を外しました。', memo: '採点メモを削除しました。', result: '自己評価を削除しました。' };
        status.textContent = messages[key];
      } catch {
        status.textContent = storageError;
      }
    }

    function listGroup(title, entries, emptyText) {
      const section = document.createElement('section');
      const heading = document.createElement('h2');
      heading.textContent = title;
      section.appendChild(heading);
      if (!entries.length) {
        const empty = document.createElement('p');
        empty.className = 'practice-muted';
        empty.textContent = emptyText;
        section.appendChild(empty);
        return section;
      }
      const list = document.createElement('ul');
      list.className = 'practice-review-items';
      for (const entry of entries) {
        const item = document.createElement('li');
        const meta = document.createElement('p');
        meta.className = 'practice-muted';
        meta.textContent = [entry.subject, validDate(entry.due) ? dateLabel(entry.due) : ''].filter(Boolean).join(' · ');
        const link = document.createElement('a');
        link.href = reviewHref(entry);
        link.className = 'practice-review-lesson';
        link.textContent = entry.title;
        item.append(meta, link);
        const actions = document.createElement('div');
        actions.className = 'practice-actions';
        if (entry.memo) {
          const details = document.createElement('details');
          const summary = document.createElement('summary');
          summary.textContent = '採点メモを読む';
          const memo = document.createElement('p');
          memo.className = 'practice-memo';
          memo.textContent = entry.memo;
          details.append(summary, memo, button('メモを削除', () => remove(entry, 'memo')));
          item.appendChild(details);
        }
        if (entry.due) {
          actions.appendChild(button('予定を外す', () => remove(entry, 'due')));
          item.appendChild(actions);
        }
        list.appendChild(item);
      }
      section.appendChild(list);
      return section;
    }

    function reviewTrends(records) {
      const section = document.createElement('section');
      const heading = document.createElement('h2');
      heading.textContent = '詰まった問題';
      const explanation = document.createElement('p');
      explanation.className = 'practice-muted';
      const subjects = new Map();
      for (const record of records) {
        if (record.result !== 'retry') continue;
        const subject = record.subject || '教材';
        if (!subjects.has(subject)) subjects.set(subject, []);
        subjects.get(subject).push(record);
      }
      explanation.textContent = subjects.size
        ? '最後の自己評価が「詰まった」の問題です。似た問題を続けて見たいときに使えます。'
        : '最後の自己評価が「詰まった」の問題はありません。';
      section.append(heading, explanation);
      for (const [subject, entries] of subjects) {
        const group = document.createElement('details');
        group.className = 'practice-trend';
        const summary = document.createElement('summary');
        summary.textContent = `${subject}（${entries.length}件）`;
        const list = document.createElement('ul');
        for (const entry of entries) {
          const row = document.createElement('li');
          const link = document.createElement('a');
          link.href = reviewHref(entry);
          link.textContent = entry.unit ? `${entry.unit} · ${entry.title}` : entry.title;
          row.append(link, button('評価を消す', () => remove(entry, 'result')));
          list.appendChild(row);
        }
        group.append(summary, list);
        section.appendChild(group);
      }
      return section;
    }

    function render() {
      try {
        const records = [];
        for (let index = 0; index < localStorage.length; index++) {
          const key = localStorage.key(index);
          if (!key?.startsWith(prefix)) continue;
          const record = parseRecord(localStorage.getItem(key), key.slice(prefix.length));
          if (record) records.push(record);
        }
        const due = records.filter(record => validDate(record.due));
        due.sort((a, b) => a.due.localeCompare(b.due) || a.title.localeCompare(b.title, 'ja'));
        const today = day();
        const pending = due.filter(record => record.due <= today);
        const later = due.filter(record => record.due > today);
        const notes = records.filter(record => !validDate(record.due) && record.memo);
        const groups = [
          listGroup(`今日までの復習（${pending.length}件）`, pending, '期限を迎えた復習はありません。'),
          listGroup(`明日以降の復習（${later.length}件）`, later, '教材で復習を記録すると、次の予定がここに並びます。'),
          reviewTrends(records)
        ];
        if (notes.length) groups.push(listGroup('予定を付けていない採点メモ', notes, ''));
        view.replaceChildren(...groups);
      } catch {
        status.textContent = storageError;
      }
    }

    mount.tabIndex = -1;
    render();
    watch('', render);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) render();
    });
  }

  document.querySelectorAll('article.lesson').forEach(initLesson);
  document.querySelectorAll('[data-review-list]').forEach(initReview);
})();
