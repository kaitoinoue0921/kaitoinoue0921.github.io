/* =========================================================================
   コメント欄 — 閲覧者どうしでコメント・返信し合う共通ウィジェット
   -------------------------------------------------------------------------
   ページの下に置くとき:
     <div data-kcom data-skin="paper"></div>
     <script src="/comments/comments.js" defer></script>
   data-kcom に値を書けばそれがスレッド名。空ならページのパス（/works/ など）。

   JS から置くとき（スタディMAPの施設ごと）:
     KComments.mount(el, 'study-map/' + spotId, 'dark');

   保存先は study-map と同じ Supabase の comments テーブル。
   テーブルの作り方は同じフォルダの comments-schema.sql。
   ========================================================================= */
(function () {
  'use strict';

  var DB = {
    url: 'https://dlodldpdrlvpweqvwidp.supabase.co',
    key: 'sb_publishable_mtrFLgfGGTqvVrennVD3Tw_jVPEKhbD'
  };
  var NAME_KEY = 'kcom.name', COOL_MS = 20000;

  var CSS = [
    '.kcom{--c-ink:#121212;--c-soft:#3a3a3a;--c-faint:#8f8f8f;--c-line:rgba(18,18,18,.14);',
    '--c-panel:#fff;--c-accent:#121212;--c-on:#fff;--c-r:10px;',
    "font-family:'Zen Kaku Gothic New','Hiragino Sans','Noto Sans JP',system-ui,sans-serif;",
    'color:var(--c-soft);font-size:14px;line-height:1.8;margin:32px 0 8px}',
    '.kcom--paper{--c-r:0}',
    '.kcom--dark{--c-ink:#e8edf2;--c-soft:#c2ccd6;--c-faint:#8c98a5;--c-line:rgba(255,255,255,.14);',
    '--c-panel:#171b1f;--c-accent:#3fbf8f;--c-on:#08130f}',
    '@media (prefers-color-scheme:dark){.kcom--auto{--c-ink:#e8edf2;--c-soft:#c2ccd6;--c-faint:#8c98a5;',
    '--c-line:rgba(255,255,255,.14);--c-panel:#171b1f;--c-accent:#3fbf8f;--c-on:#08130f}}',
    '.kcom h3{font-size:15px;color:var(--c-ink);margin:0 0 10px;font-weight:700}',
    '.kcom h3 small{font-weight:400;color:var(--c-faint);margin-left:6px;font-size:12px}',
    '.kcom form{display:grid;gap:8px;margin:0 0 16px}',
    '.kcom input,.kcom textarea{font:inherit;color:var(--c-ink);background:var(--c-panel);',
    'border:1px solid var(--c-line);border-radius:var(--c-r);padding:8px 10px;width:100%;box-sizing:border-box}',
    '.kcom textarea{min-height:72px;resize:vertical}',
    '.kcom .row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}',
    '.kcom .row input{flex:1;min-width:120px}',
    '.kcom button{font:inherit;cursor:pointer;border-radius:var(--c-r)}',
    '.kcom .send{background:var(--c-accent);color:var(--c-on);border:0;padding:8px 16px;font-weight:700}',
    '.kcom .send:disabled{opacity:.5;cursor:default}',
    '.kcom .msg{font-size:12px;color:var(--c-faint);margin:0}',
    /* ページ側の li / p / ul の飾りを打ち消す */
    '.kcom.kcom ul,.kcom.kcom li,.kcom.kcom p,.kcom.kcom h3{background:none;box-shadow:none;border:0;',
    'border-radius:0;margin:0;padding:0;max-width:none;width:auto;font-family:inherit}',
    '.kcom.kcom li::before,.kcom.kcom li::marker,.kcom.kcom p::before,.kcom.kcom h3::before{content:none}',
    '.kcom h3{margin:0 0 10px!important}',
    '.kcom ul{list-style:none;margin:0;padding:0}',
    '.kcom.kcom li{border-top:1px solid var(--c-line);padding:10px 0}',
    '.kcom.kcom li li{border-top:0;border-left:2px solid var(--c-line);padding:6px 0 6px 12px;margin-top:6px}',
    '.kcom .who{font-size:12px;color:var(--c-faint)}',
    '.kcom .who b{color:var(--c-ink);font-weight:700;margin-right:6px}',
    '.kcom .body{white-space:pre-wrap;word-break:break-word;color:var(--c-soft);margin:2px 0}',
    '.kcom .acts button{background:none;border:0;color:var(--c-faint);font-size:12px;padding:0;margin-right:12px}',
    '.kcom .acts button:hover{color:var(--c-ink)}',
    '.kcom .empty{color:var(--c-faint);font-size:13px}',
    '.kcom.kcom .note{font-size:11px;color:var(--c-faint);margin:8px 0 0}'
  ].join('');

  function css() {
    if (document.getElementById('kcom-css')) return;
    var s = document.createElement('style'); s.id = 'kcom-css'; s.textContent = CSS;
    document.head.appendChild(s);
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function ls(k, v) {
    try { if (v === undefined) return localStorage.getItem(k) || ''; localStorage.setItem(k, v); } catch (e) { return ''; }
  }
  function when(t) {
    var d = new Date(t), s = (Date.now() - d) / 1000;
    if (s < 60) return 'たった今';
    if (s < 3600) return Math.floor(s / 60) + '分前';
    if (s < 86400) return Math.floor(s / 3600) + '時間前';
    if (s < 86400 * 30) return Math.floor(s / 86400) + '日前';
    return d.getFullYear() + '/' + (d.getMonth() + 1) + '/' + d.getDate();
  }
  function api(path, opt) {
    opt = opt || {};
    var h = { apikey: DB.key, Authorization: 'Bearer ' + DB.key, 'Content-Type': 'application/json' };
    if (opt.prefer) h.Prefer = opt.prefer;
    return fetch(DB.url + '/rest/v1/' + path, { method: opt.method || 'GET', headers: h, body: opt.body })
      .then(function (r) {
        return r.text().then(function (t) {
          var j = t ? JSON.parse(t) : null;
          if (!r.ok) { var e = new Error((j && j.message) || ('HTTP ' + r.status)); e.status = r.status; throw e; }
          return j;
        });
      });
  }
  function why(e) {
    var m = String(e && e.message || '');
    if (/no_url/.test(m)) return 'URLを含むコメントは送れません（宣伝よけ）。';
    if (/duplicate/.test(m)) return '同じ内容がすでに投稿されています。';
    if (/too many/.test(m)) return '投稿が混み合っています。少し待ってからもう一度どうぞ。';
    if (/Failed to fetch|NetworkError|Load failed/.test(m)) return 'サーバーに繋がりませんでした。通信状態を確かめてもう一度どうぞ。';
    if (e && e.status === 404) return 'コメント欄の準備がまだ済んでいません。';
    return '送れませんでした（' + m + '）';
  }

  function mount(el, page, skin) {
    if (!el || el.__kcom) return; el.__kcom = 1;
    css();
    page = String(page || location.pathname.replace(/index\.html$/, '')).slice(0, 160);
    el.className = (el.className + ' kcom kcom--' + (skin || 'auto')).trim();
    el.innerHTML =
      '<h3>コメント<small></small></h3>' +
      formHTML('') +
      '<ul class="list"><li class="empty">読み込み中…</li></ul>' +
      '<p class="note">投稿はすぐ表示されます。URLは書けません。困った投稿は「通報」を押すと、何件かたまったところで隠れます。</p>';
    var list = el.querySelector('.list'), count = el.querySelector('h3 small');
    bind(el.querySelector('form'), null);

    function formHTML(parent) {
      return '<form data-parent="' + esc(parent) + '">' +
        '<textarea name="body" maxlength="800" required placeholder="' +
        (parent ? '返信を書く' : 'ここについて、ほかの人と話したいこと') + '"></textarea>' +
        '<div class="row"><input name="name" maxlength="30" placeholder="名前（空なら名無し）" value="' + esc(ls(NAME_KEY)) + '">' +
        '<button class="send" type="submit">' + (parent ? '返信する' : '投稿する') + '</button></div>' +
        '<p class="msg" aria-live="polite"></p></form>';
    }

    function bind(f, parent) {
      f.addEventListener('submit', function (ev) {
        ev.preventDefault();
        var btn = f.querySelector('.send'), msg = f.querySelector('.msg');
        var body = f.body.value.trim(), name = f.name.value.trim();
        if (!body) return;
        var last = +ls('kcom.last') || 0;
        if (Date.now() - last < COOL_MS) { msg.textContent = '続けての投稿は20秒ほど空けてください。'; return; }
        btn.disabled = true; msg.textContent = '送信中…';
        ls(NAME_KEY, name);
        api('comments', {
          method: 'POST', prefer: 'return=minimal',
          body: JSON.stringify({ page: page, parent_id: parent, name: name || null, body: body })
        }).then(function () {
          ls('kcom.last', String(Date.now()));
          f.body.value = ''; msg.textContent = '';
          load();
        }).catch(function (e) { msg.textContent = why(e); })
          .then(function () { btn.disabled = false; });
      });
    }

    function item(c, kids) {
      return '<li data-id="' + c.id + '"><div class="who"><b>' + esc(c.name || '名無し') + '</b>' + when(c.created_at) + '</div>' +
        '<div class="body">' + esc(c.body) + '</div>' +
        '<div class="acts">' + (c.parent_id ? '' : '<button data-a="reply">返信</button>') +
        '<button data-a="report">通報</button></div>' +
        (kids && kids.length ? '<ul>' + kids.map(function (k) { return item(k); }).join('') + '</ul>' : '') +
        '</li>';
    }

    function load() {
      return api('comments?select=id,parent_id,name,body,created_at&page=eq.' + encodeURIComponent(page) + '&order=created_at.asc&limit=500')
        .then(function (rows) {
          var tops = [], kids = {};
          rows.forEach(function (c) {
            if (c.parent_id) (kids[c.parent_id] = kids[c.parent_id] || []).push(c); else tops.push(c);
          });
          tops.reverse(); // 新しい話題を上に、返信は古い順
          count.textContent = rows.length ? rows.length + '件' : '';
          list.innerHTML = tops.length ? tops.map(function (c) { return item(c, kids[c.id]); }).join('')
            : '<li class="empty">まだコメントはありません。最初のひとことをどうぞ。</li>';
        })
        .catch(function (e) { list.innerHTML = '<li class="empty">' + esc(why(e)) + '</li>'; });
    }

    list.addEventListener('click', function (ev) {
      var b = ev.target.closest('button[data-a]'); if (!b) return;
      var li = b.closest('li'), id = li.getAttribute('data-id');
      if (b.getAttribute('data-a') === 'reply') {
        var ex = li.querySelector(':scope > form');
        if (ex) { ex.remove(); return; }
        li.insertAdjacentHTML('beforeend', formHTML(id));
        var f = li.querySelector(':scope > form'); bind(f, id); f.body.focus();
      } else {
        if (!confirm('このコメントを通報しますか？')) return;
        b.disabled = true;
        api('rpc/report_comment', { method: 'POST', body: JSON.stringify({ cid: id }) })
          .then(function () { b.textContent = '通報しました'; })
          .catch(function () { b.disabled = false; });
      }
    });

    load();
  }

  function scan() {
    var els = document.querySelectorAll('[data-kcom]');
    for (var i = 0; i < els.length; i++) mount(els[i], els[i].getAttribute('data-kcom'), els[i].getAttribute('data-skin'));
  }
  window.KComments = { mount: mount };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', scan); else scan();
})();
