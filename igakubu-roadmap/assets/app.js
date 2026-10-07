(function(){
  var KEY = 'igakubu-roadmap-v1';
  var st = {};
  try { st = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch(e) { st = {}; }
  st.checks = st.checks || {};
  function save(){ try { localStorage.setItem(KEY, JSON.stringify(st)); } catch(e){} }

  var now = new Date();
  var M = now.getMonth() + 1;
  function pad(n){ return (n < 10 ? '0' : '') + n; }
  var TODAY = now.getFullYear() + '-' + pad(M) + '-' + pad(now.getDate());
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }

  var GRADES = [['g1','高1'],['g2','高2'],['g3','高3'],['r','既卒']];
  var GRADE_NAME = {g1:'高1', g2:'高2', g3:'高3', r:'既卒'};
  var TYPE_NAME = {}; TYPES.forEach(function(t){ TYPE_NAME[t[0]] = t[1]; });
  var AREA_NAME = {}; AREAS.forEach(function(a){ AREA_NAME[a[0]] = a[1]; });

  function blockNow(g){
    var list = PLAN[g]; if (!list) return null;
    for (var i = 0; i < list.length; i++) if (list[i].months.indexOf(M) >= 0) return list[i];
    return null;
  }
  // 全体の地図（7つの時期）の列
  function colFor(g){
    if (g === 'g1') return 'c1';
    if (g === 'g2') return (M >= 4 && M <= 8) ? 'c2' : 'c3';
    if (g === 'g3' || g === 'r') {
      if (M >= 4 && M <= 6) return 'c4';
      if (M >= 7 && M <= 8) return 'c5';
      if (M >= 9 && M <= 11) return 'c6';
      return 'c7';
    }
    return null;
  }

  // 学年とタイプの選択ボタン
  function renderPickers(){
    var rows = document.querySelectorAll('.pick-row');
    for (var i = 0; i < rows.length; i++) {
      var row = rows[i], kind = row.getAttribute('data-pick');
      var opts = kind === 'grade' ? GRADES : TYPES.concat([['', 'まだ決めていない']]);
      var cur = kind === 'grade' ? (st.grade || '') : (st.type || '');
      var old = row.querySelectorAll('button'); for (var k = 0; k < old.length; k++) old[k].remove();
      opts.forEach(function(o){
        var b = document.createElement('button');
        b.type = 'button'; b.textContent = o[1];
        b.setAttribute('data-' + kind, o[0]);
        b.setAttribute('aria-pressed', cur === o[0] && (o[0] !== '' || kind === 'type') ? 'true' : 'false');
        row.appendChild(b);
      });
    }
  }

  function taskList(block){
    var h = '';
    AREAS.forEach(function(a){
      var tasks = block[a[0]] || [];
      if (!tasks.length) return;
      h += '<div class="area"><b>' + esc(a[1]) + '</b><ul class="checks">';
      tasks.forEach(function(t, i){
        h += '<li><label><input type="checkbox" data-id="' + block.id + '-' + a[0] + '-' + i + '"><span>' + esc(t) + '</span></label></li>';
      });
      h += '</ul></div>';
    });
    return h;
  }
  function typeNotes(t){
    if (!t) return '';
    var h = '';
    TYPES.forEach(function(ty){
      if (!t[ty[0]]) return;
      if (st.type && st.type !== ty[0]) return;
      h += '<p class="tnote"><b>' + esc(ty[1]) + '</b>' + esc(t[ty[0]]) + '</p>';
    });
    return h;
  }

  function fmt(iso){ var p = iso.split('-'); return (+p[1]) + '月' + (+p[2]) + '日'; }
  function daysUntil(iso){ return Math.round((new Date(iso + 'T00:00:00') - new Date(TODAY + 'T00:00:00')) / 86400000); }

  // トップページ：いまの場所
  function renderNow(){
    var box = document.getElementById('now-body');
    var g = st.grade;
    var col = colFor(g);
    var marks = document.querySelectorAll('.roadmap [data-col], .goal[data-col]');
    for (var j = 0; j < marks.length; j++) marks[j].classList.toggle('now', !!col && marks[j].getAttribute('data-col') === col);
    if (!box || !g) return;

    var b = blockNow(g);
    var h = '';
    if (b) {
      h += '<p class="now-title">いまは「' + esc(b.label) + '」です</p>';
      h += taskList(b) + typeNotes(b.t);
      h += '<p class="note"><a href="plan.html#' + b.id + '">月ごとの計画で前後の月を見る</a>　<a href="units.html">科目の単元ごとの目安を見る</a></p>';
    }
    var goal = document.getElementById('goal-' + col);
    if (goal) {
      h += '<h4>' + esc(goal.querySelector('h3').firstChild.textContent.trim()) + 'の目安</h4><ul class="checks">';
      var items = goal.querySelectorAll('li');
      for (var q = 0; q < items.length; q++) {
        var inp = items[q].querySelector('input');
        h += '<li><label><input type="checkbox" data-id="' + inp.getAttribute('data-id') + '"><span>' + esc(items[q].textContent.trim()) + '</span></label></li>';
      }
      h += '</ul>';
    }
    if (g === 'g3' || g === 'r') {
      var up = DEADLINES.filter(function(d){ return d.e >= TODAY; })
        .sort(function(a, c){ return a.e < c.e ? -1 : a.e > c.e ? 1 : 0; }).slice(0, 5);
      h += '<h4>次の締切と試験</h4>';
      if (up.length) {
        h += '<ul class="deadlines">';
        up.forEach(function(d){
          var when = d.s === d.e ? fmt(d.e) : (d.s <= TODAY ? fmt(d.e) + 'まで' : fmt(d.s) + '〜' + fmt(d.e));
          h += '<li class="' + (daysUntil(d.e) <= 7 ? 'soon' : '') + '"><span class="d">' + when + '</span><span>' + esc(d.t) + (d.n ? '<br><span class="note">' + esc(d.n) + '</span>' : '') + '</span></li>';
        });
        h += '</ul><p class="note">2027年度入試の日程です。必ず公式の要項で確認してください。</p>';
      } else {
        h += '<p class="note">このページに載せている2027年度入試の日程は終わりました。新しい年度の日程は各大学の要項で確認してください。</p>';
      }
    }
    box.innerHTML = h;
  }

  // 月ごとの計画ページ
  function renderPlan(){
    var box = document.getElementById('plan');
    if (!box) return;
    var g = st.grade || 'g3';
    var cur = blockNow(g);
    var h = '';
    if (!st.grade) h += '<p class="note">学年が選ばれていないので、高3の計画を表示しています。</p>';
    if (cur) h += '<p><a href="#' + cur.id + '">いまの時期「' + esc(cur.label) + '」へ移動</a></p>';
    PLAN[g].forEach(function(b){
      h += '<section class="block' + (cur && cur.id === b.id ? ' now' : '') + '" id="' + b.id + '"><h3>' + esc(b.label) +
        (cur && cur.id === b.id ? '<span class="badge">いま</span>' : '') + '<span class="prog" data-prog="' + b.id + '"></span></h3>' +
        taskList(b) + typeNotes(b.t) + '</section>';
    });
    box.innerHTML = h;
    var title = document.getElementById('plan-title');
    if (title) title.textContent = GRADE_NAME[g] + 'の月ごとの計画';
  }

  // 単元ページ
  function renderUnits(){
    var box = document.getElementById('units');
    if (!box) return;
    var key = (location.hash || '').slice(1);
    if (!UNITS.some(function(u){ return u.key === key; })) key = st.subj || 'math';
    st.subj = key;
    var tabs = '<div class="tabs" role="tablist">';
    UNITS.forEach(function(u){
      tabs += '<button type="button" role="tab" data-subj="' + u.key + '" aria-selected="' + (u.key === key) + '">' + esc(u.name) + '</button>';
    });
    tabs += '</div>';
    var u = UNITS.filter(function(x){ return x.key === key; })[0];
    var h = tabs + '<p>' + esc(u.intro) + '</p>';
    if (u.link) h += '<p class="note"><a href="' + u.link.href + '" target="_blank" rel="noopener">' + esc(u.link.text) + '</a></p>';
    var no = 0;
    u.groups.forEach(function(gr, gi){
      h += '<p class="group-title">' + esc(gr.name) + '</p>';
      gr.items.forEach(function(it, ii){
        no++;
        var id = 'u-' + key + '-' + gi + '-' + ii;
        h += '<div class="unit"><div class="unit-head"><span class="no">' + no + '</span><label><input type="checkbox" data-id="' + id + '"><span>' + esc(it.n) + '</span></label><span class="when" style="font-size:.82rem;color:var(--now);font-weight:700">' + esc(it.when) + '</span></div>';
        h += '<p><span class="lbl">終えた基準</span>' + esc(it.goal) + '</p>';
        if (it.tip) h += '<p><span class="lbl">つまずき</span>' + esc(it.tip) + '</p>';
        if (it.med) h += '<p class="why"><span class="lbl">医学部では</span>' + esc(it.med) + '</p>';
        h += typeNotes(it.t);
        h += '</div>';
      });
    });
    box.innerHTML = h;
  }

  function syncChecks(){
    var boxes = document.querySelectorAll('input[type=checkbox][data-id]');
    for (var i = 0; i < boxes.length; i++) boxes[i].checked = !!st.checks[boxes[i].getAttribute('data-id')];
    var groups = document.querySelectorAll('.goal, .block');
    for (var j = 0; j < groups.length; j++) {
      var all = groups[j].querySelectorAll('input[data-id]'), done = 0;
      for (var k = 0; k < all.length; k++) if (all[k].checked) done++;
      var p = groups[j].querySelector('.prog');
      if (p) p.textContent = all.length ? done + ' / ' + all.length : '';
    }
  }

  function renderAll(){
    renderPickers(); renderNow(); renderPlan(); renderUnits(); syncChecks();
  }

  document.addEventListener('click', function(e){
    var b = e.target.closest && e.target.closest('button');
    if (!b) return;
    if (b.hasAttribute('data-grade')) { st.grade = b.getAttribute('data-grade'); save(); renderAll(); }
    else if (b.hasAttribute('data-type')) { st.type = b.getAttribute('data-type'); save(); renderAll(); }
    else if (b.hasAttribute('data-subj')) { st.subj = b.getAttribute('data-subj'); history.replaceState(null, '', '#' + st.subj); save(); renderUnits(); syncChecks(); }
  });
  document.addEventListener('change', function(e){
    var t = e.target;
    if (!t.matches || !t.matches('input[type=checkbox][data-id]')) return;
    st.checks[t.getAttribute('data-id')] = t.checked;
    save(); syncChecks();
  });
  renderAll();
  // 計画ページでは、いまの時期（またはURLの#で指定した月）へ移動する
  if (document.getElementById('plan')) {
    if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
    window.addEventListener('load', function(){
      var id = location.hash ? location.hash.slice(1) : ((blockNow(st.grade || 'g3') || {}).id);
      var el = id && document.getElementById(id);
      if (el) setTimeout(function(){ el.scrollIntoView({block:'start'}); }, 0);
    });
  }
})();
