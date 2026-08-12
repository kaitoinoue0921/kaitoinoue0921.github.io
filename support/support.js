/* =========================================================================
   応援セクション — 作ったもの共通ウィジェット
   -------------------------------------------------------------------------
   各ページはマウント用の div を置いて、このファイルを読むだけ。

     <div data-ksup="todai-math-map" data-skin="auto"></div>
     <script src="/support/support.js" defer></script>

   ダイアログとして開きたいとき（全画面アプリなど）はマウントを置かず、
   任意のボタンから KSupport.open('study-map', 'dark') を呼ぶ。

   data-skin:
     paper … プロフィールサイト（白・明朝・角丸なし）
     light … 常時ライト（GADGET LOG など、ライト固定のページ）
     auto  … 端末のライト/ダークに追従（既定）
     dark  … 常時ダーク

   ★ 編集するのは下の「設定」ブロックだけ。
   ========================================================================= */
(function () {
  'use strict';

  /* ======================== 設定 ======================== */

  /* 投げ銭の決済リンク（Stripe）。url に https://buy.stripe.com/... を貼れば
     ボタンが出る。空のあいだは「準備中」とだけ表示してボタンは出さない。

     使っているのは「¥100 × 数量」で金額を決めるリンク 1 本。
     決済画面の数量が金額になるので、その読み方を hint に書いておく。
     リンクは 1 本で足りる。どの作品からの支援かは client_reference_id で
     自動的に振り分けられ、Stripe の決済詳細に作品IDとして出る。 */
  var TIP = {
    url:  'https://donate.stripe.com/eVq7sKcxmfNu3ej4lJ5ZC00',
    hint: '決済画面の「数量」がそのまま金額になります（1 = ¥100、100 = ¥10,000）。'
  };

  /* 応援メッセージの保存先。study-map と同じ共有DBを使う。
     publishable key は公開前提の鍵なので、ここに書いて問題ない（RLS で守る）。
     空にすればメール送信にフォールバックする。 */
  var SUPABASE = {
    url: 'https://dlodldpdrlvpweqvwidp.supabase.co',
    key: 'sb_publishable_mtrFLgfGGTqvVrennVD3Tw_jVPEKhbD'
  };

  /* Supabase 未設定のときの送り先 */
  var CONTACT_MAIL = 'kaito.inoue0921@gmail.com';

  /* 作品ごとの文面。ここに 1 行足せば、その作品の応援セクションが作れる。
     cta … ボタンの文言（省略時は「投げ銭で応援する」）
     ph  … 感想フォームの例文（省略時は下の PLACEHOLDER） */
  var CTA = '投げ銭で応援する';
  var PLACEHOLDER = '例）ここが分かりにくかった、こういう機能がほしい、など。';

  var WORKS = {
    'site': {
      title: '実際に寄付する',
      cta: '寄付する',
      lead: '金額はいくらでもかまいませんし、寄付しないまま使い続けてもらってもまったく問題ありません。',
      use: '受け取ったぶんは、サーバーと API の実費、実機の購入費、そして次を作る時間に充てます。'
    },
    'works': {
      title: '作ったものを応援する',
      lead: 'ここに置いているものは、すべて個人で作って個人で運営しています。広告は入れていません。'
          + '役に立ったと思ってもらえたら、応援していただけると続けやすくなります。',
      use: 'いただいたぶんは、サーバー代と API の実費、それから次を作る時間に充てます。'
    },
    'study-map': {
      title: 'スタディスポットMAPを応援する',
      ph: '例）駐車場の有無も分かると助かります。',
      lead: '無料で勉強できる場所を集めた地図です。個人で作って、個人で運営しています。広告は入れていません。',
      use: '共有データベースと地図 API の実費で動いています。'
         + '掲載を栃木県の外へ広げるほど、地図の読み込みとデータ量がそのまま増えます。'
    },
    'todai-math-map': {
      title: '数学マップを応援する',
      lead: '数学の全範囲を依存グラフに組み直した学習マップです。個人で作っています。広告は入れていません。',
      use: 'サーバー代はほとんどかかっていません。足りていないのは時間のほうで、'
         + '統合解説はまだ 138 ノード中 6 つです。残りを書く時間に充てます。'
    },
    'gadget-log': {
      title: 'GADGET LOGを応援する',
      lead: 'レビューは、実機を買うか借りるかして、使ってから書いています。',
      use: '次に試す機材の購入費とレンタル代に充てます。試せる数がそのまま記事の数になります。'
    },
    'machinokoe': {
      title: 'まちのコエを応援する',
      lead: '住民の困りごとを共有して、賛同が集まったら行政提出用の提案書を自動で作る、非営利のシビックテック・プラットフォームです。個人で作って、個人で運営しています。広告は入れていません。',
      use: '寄付だけで運営費（サーバーとAPIの実費）を賄う設計です。いまはデータを端末内に保存するだけのプロトタイプで、実際の寄付や運用はこれからです。'
    }
  };

  /* ====================== 設定ここまで ====================== */

  var MOUNT_ATTR = 'data-ksup';
  var injected = false;
  var seq = 0;

  function esc(t) {
    return String(t == null ? '' : t).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* 各ページの「投げ銭で応援する」は、いきなりStripeの決済画面に飛ばさず、
     まず /support/ の説明ページに送る。何に使うか・誰が作っているかを読んだ
     うえで払ってもらうほうが、決済画面だけを見せるより実際に押されやすいため。
     /support/ ページ自身ではこの中継はせず、そのままStripeへ飛ばす。 */
  function isDonatePage() {
    return /\/support\/(?:index\.html)?$/.test(location.pathname);
  }

  /* 決済リンクに作品 ID を載せる。Stripe の決済詳細に client_reference_id として残るので、
     リンクが 1 本でも、どの作品への支援かが後から分かる。
     使えるのは英数字・ダッシュ・アンダースコアだけなので、作品IDもその範囲で付ける。
     /support/ に中継されたあとは、どの作品から来たかを ?from= から引き継ぐ。 */
  function tipHref(workId) {
    if (!TIP.url) return '';
    if (!isDonatePage()) return '/support/?from=' + encodeURIComponent(workId);
    var from = new URLSearchParams(location.search).get('from') || workId;
    return TIP.url + (TIP.url.indexOf('?') === -1 ? '?' : '&')
      + 'client_reference_id=' + encodeURIComponent(from);
  }

  /* ---------------------------------------------------------------- CSS */

  var CSS = [
    '.ksup{--ksup-bg:transparent;--ksup-panel:#fff;--ksup-ink:#121212;--ksup-soft:#3a3a3a;',
    '--ksup-faint:#8f8f8f;--ksup-line:rgba(18,18,18,0.14);--ksup-accent:#121212;',
    '--ksup-on-accent:#fff;--ksup-radius:12px;',
    "--ksup-sans:'Zen Kaku Gothic New','Hiragino Sans','Noto Sans JP',system-ui,sans-serif;",
    "--ksup-serif:'Shippori Mincho',serif;--ksup-mono:'JetBrains Mono',ui-monospace,monospace;",
    'font-family:var(--ksup-sans);color:var(--ksup-soft);line-height:1.9;font-size:15px;',
    'text-align:left;box-sizing:border-box}',
    '.ksup *,.ksup *::before,.ksup *::after{box-sizing:border-box}',

    /* --- skins --- */
    '.ksup--paper{--ksup-radius:0}',
    '.ksup--dark{--ksup-panel:#171b1f;--ksup-ink:#e8edf2;--ksup-soft:#c2ccd6;--ksup-faint:#8c98a5;',
    '--ksup-line:rgba(255,255,255,0.14);--ksup-accent:#3fbf8f;--ksup-on-accent:#08130f;',
    '--ksup-serif:var(--ksup-sans)}',
    '@media (prefers-color-scheme:dark){',
    '.ksup--auto{--ksup-panel:#171a21;--ksup-ink:#e6e9ef;--ksup-soft:#c3c9d4;--ksup-faint:#98a0b0;',
    '--ksup-line:rgba(255,255,255,0.14);--ksup-accent:#6ea8fe;--ksup-on-accent:#0b1220;',
    '--ksup-serif:var(--ksup-sans)}}',
    '.ksup--auto{--ksup-accent:#2b6cd4;--ksup-on-accent:#fff;--ksup-serif:var(--ksup-sans)}',
    '.ksup--light{--ksup-accent:#2a5bd7;--ksup-on-accent:#fff;--ksup-serif:var(--ksup-sans)}',

    /* --- head --- */
    '.ksup__label{font-family:var(--ksup-mono);font-size:11.5px;letter-spacing:.16em;',
    'text-transform:uppercase;color:var(--ksup-faint);margin:0 0 10px}',
    '.ksup__title{font-family:var(--ksup-serif);font-weight:700;color:var(--ksup-ink);',
    'font-size:clamp(19px,2.6vw,24px);line-height:1.5;margin:0 0 16px;letter-spacing:.02em}',
    '.ksup__lead{margin:0 0 14px;max-width:58ch}',
    '.ksup__use{margin:0;max-width:58ch;font-size:13.5px;color:var(--ksup-faint);',
    'border-left:2px solid var(--ksup-line);padding-left:14px}',

    /* --- tip button --- */
    '.ksup__tip{display:inline-flex;align-items:center;gap:10px;margin:26px 0 0;',
    'text-decoration:none;border:1px solid var(--ksup-accent);background:var(--ksup-accent);',
    'color:var(--ksup-on-accent);border-radius:var(--ksup-radius);padding:14px 30px;',
    'font-size:15px;font-weight:600;letter-spacing:.02em;',
    'transition:opacity .2s ease,transform .2s ease}',
    '.ksup__tip:hover{opacity:.88;transform:translateY(-2px)}',
    '.ksup__tip:active{transform:translateY(0)}',
    '.ksup__tip:focus-visible{outline:2px solid var(--ksup-accent);outline-offset:3px}',
    '.ksup__tip svg{width:15px;height:15px;flex-shrink:0;fill:none;stroke:currentColor}',
    '.ksup__pending{display:inline-block;margin:26px 0 0;font-family:var(--ksup-mono);',
    'font-size:12px;letter-spacing:.12em;color:var(--ksup-faint);',
    'border:1px dashed var(--ksup-line);border-radius:var(--ksup-radius);padding:12px 18px}',
    '.ksup__fee{margin:12px 0 0;font-size:12.5px;color:var(--ksup-faint);max-width:52ch;line-height:1.85}',

    /* --- form --- */
    '.ksup__formhead{margin:34px 0 0;font-size:13.5px;color:var(--ksup-soft);max-width:58ch}',
    '.ksup__form{margin:14px 0 0;max-width:520px}',
    '.ksup__field{margin:0 0 12px}',
    '.ksup__field label{display:block;font-family:var(--ksup-mono);font-size:10.5px;',
    'letter-spacing:.16em;text-transform:uppercase;color:var(--ksup-faint);margin:0 0 6px}',
    '.ksup__field input,.ksup__field textarea{width:100%;background:var(--ksup-bg);',
    'border:1px solid var(--ksup-line);border-radius:var(--ksup-radius);color:var(--ksup-ink);',
    'font-family:inherit;font-size:15px;line-height:1.8;padding:11px 13px;-webkit-appearance:none}',
    '.ksup__field textarea{min-height:104px;resize:vertical}',
    '.ksup__field input:focus,.ksup__field textarea:focus{outline:none;border-color:var(--ksup-accent)}',
    /* 投げ銭ボタンを主役にしたいので、送信ボタンは輪郭だけの二番手にしておく */
    '.ksup__submit{border:1px solid var(--ksup-line);background:transparent;',
    'color:var(--ksup-ink);border-radius:var(--ksup-radius);font-family:inherit;',
    'font-size:14px;font-weight:600;padding:12px 26px;cursor:pointer;',
    'transition:border-color .2s ease,opacity .2s ease}',
    '.ksup__submit:hover{border-color:var(--ksup-accent)}',
    '.ksup__submit:focus-visible{outline:2px solid var(--ksup-accent);outline-offset:3px}',
    '.ksup__submit:disabled{opacity:.45;cursor:not-allowed}',
    '.ksup__status{margin:10px 0 0;font-size:13px;color:var(--ksup-faint);min-height:1.2em}',

    /* --- messages --- */
    '.ksup__msgs{list-style:none;margin:26px 0 0;padding:0;border-top:1px solid var(--ksup-line)}',
    '.ksup__msgs li{border-bottom:1px solid var(--ksup-line);padding:14px 2px}',
    '.ksup__meta{display:flex;gap:10px;align-items:center;margin:0 0 4px;',
    'font-family:var(--ksup-mono);font-size:10.5px;letter-spacing:.1em;color:var(--ksup-faint)}',
    '.ksup__badge{border:1px solid var(--ksup-line);border-radius:99px;padding:1px 8px}',
    '.ksup__body{margin:0;font-size:14px;line-height:1.9;color:var(--ksup-soft);',
    'white-space:pre-wrap;overflow-wrap:anywhere}',

    /* --- dialog --- */
    '.ksup-overlay{position:fixed;inset:0;z-index:99999;display:flex;align-items:flex-end;',
    'justify-content:center;background:rgba(0,0,0,.55);padding:0;overscroll-behavior:contain}',
    '@media (min-width:640px){.ksup-overlay{align-items:center;padding:24px}}',
    '.ksup-dialog{background:var(--ksup-panel);color:var(--ksup-soft);width:100%;',
    'max-width:620px;max-height:88vh;overflow-y:auto;-webkit-overflow-scrolling:touch;',
    'border-radius:16px 16px 0 0;padding:26px 22px 34px;position:relative}',
    '@media (min-width:640px){.ksup-dialog{border-radius:16px;padding:32px 34px 38px}}',
    '.ksup-close{position:absolute;top:12px;right:12px;width:36px;height:36px;line-height:1;',
    'font-size:20px;background:transparent;border:1px solid var(--ksup-line);border-radius:50%;',
    'color:var(--ksup-faint);cursor:pointer}',
    '.ksup-close:hover{color:var(--ksup-ink)}',

    '@media (prefers-reduced-motion:reduce){.ksup *{transition:none!important}}'
  ].join('');

  function injectCSS() {
    if (injected) return;
    injected = true;
    var s = document.createElement('style');
    s.setAttribute('data-ksup-style', '');
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  /* -------------------------------------------------------------- markup */

  function buildHTML(workId, work) {
    var id = 'ksup' + (++seq);
    var onDonatePage = isDonatePage();

    var tipHTML = TIP.url
      ? '<a class="ksup__tip" href="' + esc(tipHref(workId)) + '"'
        + (onDonatePage ? ' target="_blank" rel="noopener noreferrer"' : '')
        + '>'
        + '<span>' + esc(work.cta || CTA) + '</span>'
        + '<svg viewBox="0 0 16 16" aria-hidden="true">'
        + '<path d="M4 12 L12 4 M6 4 H12 V10" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        + '</svg></a>'
        + (onDonatePage
          ? '<p class="ksup__fee">' + esc(TIP.hint)
            + '<br>決済は Stripe を通します。カード情報がこちらに渡ることはありません。</p>'
          : '<p class="ksup__fee">金額や使い道を書いた寄付ページに移動します。決済（Stripe）はそちらから行えます。</p>')
      : '<p class="ksup__pending">投げ銭リンクは準備中です</p>';

    return ''
      + '<p class="ksup__label">Support · 応援</p>'
      + '<h2 class="ksup__title">' + esc(work.title) + '</h2>'
      + '<p class="ksup__lead">' + esc(work.lead) + '</p>'
      + '<p class="ksup__use">' + esc(work.use) + '</p>'
      + tipHTML
      + '<p class="ksup__formhead">お金を出さなくても、感想や「こういう機能がほしい」を送ってもらえれば十分助かります。'
      + 'むしろ、次に何を作るかを決めるうえではそちらのほうが効きます。</p>'
      + '<form class="ksup__form" novalidate>'
      +   '<div class="ksup__field"><label for="' + id + 'n">お名前（任意）</label>'
      +     '<input id="' + id + 'n" type="text" maxlength="40" placeholder="名無しでもOK" autocomplete="off"></div>'
      +   '<div class="ksup__field"><label for="' + id + 'b">ご意見・ご感想</label>'
      +     '<textarea id="' + id + 'b" maxlength="1000" required placeholder="' + esc(work.ph || PLACEHOLDER) + '"></textarea></div>'
      +   '<button class="ksup__submit" type="submit">送信する</button>'
      +   '<p class="ksup__status" role="status" aria-live="polite"></p>'
      + '</form>'
      + '<ul class="ksup__msgs" hidden></ul>';
  }

  /* ---------------------------------------------------------- 送信まわり */

  var sbPromise = null;

  function supabaseReady() {
    return Boolean(SUPABASE.url && SUPABASE.key);
  }

  function getSupabase() {
    if (sbPromise) return sbPromise;
    sbPromise = new Promise(function (resolve, reject) {
      if (window.supabase && window.supabase.createClient) return resolve(window.supabase);
      var s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
      s.onload = function () { resolve(window.supabase); };
      s.onerror = function () { reject(new Error('supabase-js を読み込めませんでした')); };
      document.head.appendChild(s);
    }).then(function (lib) {
      return lib.createClient(SUPABASE.url, SUPABASE.key);
    });
    return sbPromise;
  }

  /* messages.work 列がまだ無いDBでも動くようにする。
     列を足す前は work なしで保存し、足したあとは自動的に work 付きに戻る。

     列が無いときのエラーは、経路によって別物が返るので両方見る:
       select → 42703  "column messages.work does not exist"（PostgreSQL）
       insert → PGRST204 "Could not find the 'work' column ... in the schema cache"（PostgREST）
     片方だけ見ているとフォールバックが効かず、送信が失敗して終わる。 */
  var hasWorkColumn = true;

  function isMissingWorkColumn(err) {
    if (!err) return false;
    if (err.code === '42703' || err.code === 'PGRST204') return true;
    return /\bwork\b/.test(err.message || '')
      && /(does not exist|could not find)/i.test(err.message || '');
  }

  function insertMessage(sb, workId, name, body) {
    var row = { name: name || null, body: body };
    if (hasWorkColumn) row.work = workId;
    return sb.from('messages').insert(row).then(function (res) {
      if (res && res.error && hasWorkColumn && isMissingWorkColumn(res.error)) {
        hasWorkColumn = false;
        return insertMessage(sb, workId, name, body);
      }
      return res;
    });
  }

  function mailtoFallback(workId, work, name, body) {
    var subject = '【応援】' + work.title;
    var lines = [];
    if (name) lines.push('お名前: ' + name);
    lines.push('作品: ' + work.title + '（' + workId + '）');
    lines.push('');
    lines.push(body);
    return 'mailto:' + CONTACT_MAIL
      + '?subject=' + encodeURIComponent(subject)
      + '&body=' + encodeURIComponent(lines.join('\n'));
  }

  function wire(root, workId, work) {
    var form   = root.querySelector('.ksup__form');
    var name   = root.querySelector('.ksup__field input');
    var body   = root.querySelector('.ksup__field textarea');
    var status = root.querySelector('.ksup__status');
    var submit = root.querySelector('.ksup__submit');
    var list   = root.querySelector('.ksup__msgs');

    if (!supabaseReady()) {
      status.textContent = '送信するとメールアプリが開きます。そのまま送ってください。';
    }

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var text = body.value.trim();
      if (!text) { status.textContent = '本文を入力してください。'; body.focus(); return; }

      /* Supabase 未設定のあいだはメールに逃がす。公開初日から動くようにしておく。 */
      if (!supabaseReady()) {
        window.location.href = mailtoFallback(workId, work, name.value.trim(), text);
        status.textContent = 'メールアプリを開きました。送信されない場合は ' + CONTACT_MAIL + ' 宛にお願いします。';
        return;
      }

      submit.disabled = true;
      status.textContent = '送信中…';
      getSupabase().then(function (sb) {
        return insertMessage(sb, workId, name.value.trim(), text);
      }).then(function (res) {
        if (res && res.error) throw res.error;
        form.reset();
        submit.disabled = false;
        status.textContent = 'ありがとうございます。確認のうえ、掲載させていただく場合があります。';
      }).catch(function (err) {
        submit.disabled = false;
        status.textContent = '送信できませんでした: ' + ((err && err.message) || '時間をおいて試してください');
      });
    });

    /* 承認済みメッセージの表示（Supabase 設定時のみ）。
       work 列がまだ無いDBでは、作品で絞らず全件から出す。 */
    if (!supabaseReady()) return;
    getSupabase().then(function (sb) {
      function fetchMsgs(withWork) {
        var q = sb.from('messages')
          .select(withWork ? 'name, body, kind, work, created_at' : 'name, body, kind, created_at')
          .eq('approved', true);
        if (withWork) q = q.eq('work', workId);
        return q.order('created_at', { ascending: false }).limit(20).then(function (res) {
          if (res && res.error && withWork && isMissingWorkColumn(res.error)) {
            hasWorkColumn = false;
            return fetchMsgs(false);
          }
          return res;
        });
      }
      return fetchMsgs(hasWorkColumn);
    }).then(function (res) {
      var rows = res && res.data;
      if (!rows || !rows.length) return;
      list.innerHTML = rows.map(function (m) {
        return '<li><p class="ksup__meta">'
          + '<span>' + esc(m.name || '名無し') + '</span>'
          + '<span>' + esc(String(m.created_at || '').slice(0, 10)) + '</span>'
          + (m.kind === 'support' ? '<span class="ksup__badge">支援者</span>' : '')
          + '</p><p class="ksup__body">' + esc(m.body) + '</p></li>';
      }).join('');
      list.hidden = false;
    }).catch(function () { /* 表示できないだけなので黙って諦める */ });
  }

  /* ------------------------------------------------------------- 描画API */

  function render(el, workId, skin) {
    var work = WORKS[workId];
    if (!work) {
      if (window.console) console.warn('[KSupport] 未定義の作品ID: ' + workId);
      return;
    }
    injectCSS();
    el.classList.add('ksup', 'ksup--' + (skin || 'auto'));
    el.innerHTML = buildHTML(workId, work);
    wire(el, workId, work);
  }

  function open(workId, skin) {
    var work = WORKS[workId];
    if (!work) return;
    injectCSS();

    var overlay = document.createElement('div');
    overlay.className = 'ksup-overlay';

    var dialog = document.createElement('div');
    dialog.className = 'ksup ksup--' + (skin || 'auto') + ' ksup-dialog';
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-label', work.title);
    dialog.innerHTML = '<button class="ksup-close" type="button" aria-label="閉じる">×</button>'
      + buildHTML(workId, work);

    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    wire(dialog, workId, work);

    var opener = document.activeElement;
    function close() {
      overlay.remove();
      document.removeEventListener('keydown', onKey);
      if (opener && opener.focus) opener.focus();
    }
    function onKey(e) { if (e.key === 'Escape') close(); }

    dialog.querySelector('.ksup-close').addEventListener('click', close);
    overlay.addEventListener('mousedown', function (e) { if (e.target === overlay) close(); });
    document.addEventListener('keydown', onKey);
    dialog.querySelector('.ksup-close').focus();

    return close;
  }

  function mountAll() {
    var nodes = document.querySelectorAll('[' + MOUNT_ATTR + ']');
    Array.prototype.forEach.call(nodes, function (el) {
      if (el.dataset.ksupDone) return;
      el.dataset.ksupDone = '1';
      render(el, el.getAttribute(MOUNT_ATTR), el.getAttribute('data-skin'));
    });
  }

  /* ページ内のどこからでも、data-ksup-open="作品ID" を付けた要素でダイアログを開ける。
     スキンは、その要素の data-skin →ページ内のマウントの data-skin →auto の順で決まる。 */
  function bindTriggers() {
    document.addEventListener('click', function (e) {
      var t = e.target && e.target.closest ? e.target.closest('[data-ksup-open]') : null;
      if (!t) return;
      e.preventDefault();
      var mount = document.querySelector('[' + MOUNT_ATTR + '][data-skin]');
      var skin = t.getAttribute('data-skin')
        || (mount && mount.getAttribute('data-skin'))
        || 'auto';
      open(t.getAttribute('data-ksup-open'), skin);
    });
  }

  window.KSupport = { open: open, render: render, mountAll: mountAll, works: WORKS };

  bindTriggers();

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountAll);
  } else {
    mountAll();
  }
})();
