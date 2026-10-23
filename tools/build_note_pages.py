#!/usr/bin/env python3
"""高校ノート（1ファイル版）を、1項目1ページに分けて書き出す。

ノートは1ファイルに全項目が入っているので、Google から見ると「URL が1つ」しかない。
項目ごとに URL を持たせて、「モル濃度 求め方」のような検索から直接たどり着けるようにする。

  入力: works/<ノート>/index.html（触らない）
  出力: works/<ノート>/items/index.html   項目一覧
        works/<ノート>/items/patterns.html 着眼点まとめ（全項目の着眼点を単元ごとに1枚へ）
        works/<ノート>/items/<項目ID>.html 各項目
        works/<ノート>/items/note.css     ノートの見た目（ノート本体から抜き出す）
        assets/katex/                     数式の描画（全ノートで共有）
        sitemap.xml                       /items/ の行だけ作り直す

ノートを作り直したら、もう一度走らせる:
  python3 tools/build_note_pages.py
"""
import base64
import datetime
import html
import json
import re
from pathlib import Path

from tex_title import tex_plain, title_plain

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://kaitoinoue0921.github.io'
NOTES = [  # (フォルダ, ページタイトルで使う短い名前)
    ('math-notes', '高校数学ノート'),
    ('chem-notes', '高校化学ノート'),
    ('physics-notes', '高校物理ノート'),
    ('eng-grammar-notes', '英文法ノート'),
]
TIER = {'must': '必須', 'core': '差がつく', 'skip': '不要'}
TODAY = datetime.date.today().isoformat()

ADS = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?'
       'client=ca-pub-1744436882685241" crossorigin="anonymous"></script>')
GOAT = ('<script data-goatcounter="https://kaitoinoue.goatcounter.com/count" '
        'async src="//gc.zgo.at/count.js"></script>')
RENDER_JS = """(function(){function r(){if(!window.katex)return;
document.querySelectorAll('.tx:not(.r)').forEach(function(el){try{katex.render(el.textContent,el,
{displayMode:el.dataset.d==='1',throwOnError:false,strict:'ignore'})}catch(e){}el.classList.add('r')})}
if(document.readyState!=='loading')r();else document.addEventListener('DOMContentLoaded',r)})();
"""
EXTRA_CSS = """
/* ---- 1項目1ページ用（tools/build_note_pages.py が足す） ---- */
.ip-main{max-width:840px;margin:0 auto;padding:12px 16px 64px}
.crumbs{font-size:.8rem;color:var(--ink-soft);margin:10px 0 2px;line-height:1.6}
.crumbs a{color:inherit}
.ip-note{font-size:.85rem;color:var(--ink-soft);margin:4px 0 8px}
.item-foot a{font-size:.9rem}
.pn{display:flex;justify-content:space-between;gap:12px;margin:20px 0;font-size:.9rem;line-height:1.5}
.pn a{display:block;max-width:48%;padding:10px 12px;border:1px solid var(--rule);border-radius:8px;
  background:var(--surface);color:var(--ink);text-decoration:none}
.pn a small{display:block;color:var(--ink-soft);font-size:.75rem}
.pn .nx{margin-left:auto;text-align:right}
.sib h2,.ilist h2{font-size:1.05rem;margin:28px 0 8px}
.sib ol,.ilist ol{padding-left:1.7em;margin:0}
.sib li,.ilist li{margin:3px 0;line-height:1.6}
.sib li.cur{font-weight:700}
.tier-mini{font-size:.7rem;padding:0 6px;border-radius:4px;margin-left:6px;vertical-align:1px;white-space:nowrap}
.tier-mini.must{background:var(--must-soft);color:var(--must)}
.tier-mini.core{background:var(--core-soft);color:var(--core)}
.tier-mini.skip{background:var(--skip-soft);color:var(--skip)}
.ilist .grp{font-size:.8rem;color:var(--ink-soft);margin:24px 0 -4px}
.back{margin:28px 0 0;font-size:.9rem}
.ip-pat{margin:0 0 8px;font-size:.95rem}
/* 着眼点まとめ（patterns.html）: 1項目 = 項目名の行 + 着眼点の行 */
.plist .pt-list{list-style:none;padding:0;margin:0}
.plist .pt{margin:0;padding:10px 0}
.plist .pt + .pt{border-top:1px solid var(--rule)}
.plist .pt-h{margin:0;line-height:1.5}
.plist .pt-h a{font-weight:700}
.plist .pt-f{margin:4px 0 0;font-size:.95rem;line-height:1.75;overflow-wrap:anywhere}
/* 印刷はダークモードでも明るい配色にする（紙に薄い字が出ないように） */
@media print{:root,:root:not([data-theme="light"]){--bg:#fff;--surface:#fff;--surface-2:#f2f2f2;--ink:#111;--ink-soft:#444;
  --rule:#ccc;--rule-strong:#999;--must:#a6392a;--must-soft:#f4ded9;--core:#9a7425;--core-soft:#f1e6cd;--skip:#555;--skip-soft:#eee}}
@media print{
  .top,.crumbs,.site-footer,ins.adsbygoogle{display:none!important}
  .plist{max-width:none;padding:0}
  .plist h1{font-size:1.2rem}
  .plist h2,.plist .grp{break-after:avoid}
  .plist h2{margin:16px 0 4px}
  .plist .pt{break-inside:avoid;padding:5px 0}
  .plist .pt-h{font-size:.9rem}
  .plist .pt-f{font-size:.8rem;line-height:1.6}
}
"""


def esc(s):
    return html.escape(s, quote=True)


def plain(fragment, limit=None):
    """HTML 片から、説明文に使える素の文字列を作る。数式は読める形に崩す。"""
    def tex(m):
        return tex_plain(html.unescape(m.group(1)))
    s = re.sub(r'<span class="tx"[^>]*>(.*?)</span>', tex, fragment, flags=re.S)
    s = re.sub(r'<b class="bl">.*?</b>|<b>着眼点</b>', '', s)
    s = re.sub(r'</?(?:b|i|em|strong|span|sub|sup|code|u|a)(?:\s[^>]*)?>', '', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = re.sub(r'\s+', ' ', html.unescape(s)).strip()
    if limit and len(s) > limit:
        s = s[:limit - 1] + '…'
    return s


def find_block(blocks, needle):
    for b in blocks:
        if needle in b:
            return b
    return ''


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def write_katex(styles, scripts):
    """KaTeX の CSS・JS をノートから抜き出して assets/katex/ に置く。フォントは別ファイルにする。"""
    out = ROOT / 'assets' / 'katex'
    css = find_block(styles, 'font-family:KaTeX')
    js = next((b for b in scripts if 'katex' in b[:400].lower() or len(b) > 200000), '')
    mhchem = next((b for b in scripts if 'require("katex")' in b[:400]), '')
    if not (css and js and mhchem):
        return False
    n = 0

    def font(m):
        nonlocal n
        n += 1
        mime, data = m.group(1), m.group(2)
        ext = mime.split('/')[-1]
        name = f'f{n:02d}.{ext}'
        (out / 'fonts').mkdir(parents=True, exist_ok=True)
        (out / 'fonts' / name).write_bytes(base64.b64decode(data))
        return f'url(fonts/{name})'
    css = re.sub(r'url\(data:(font/[a-z0-9]+);base64,([A-Za-z0-9+/=]+)\)', font, css)
    write(out / 'katex.css', css)
    write(out / 'katex.js', js)
    write(out / 'mhchem.js', mhchem)
    write(out / 'render.js', RENDER_JS)
    return True


def page(*, title, desc, url, css_math, body, crumbs_ld, site_id):
    head_math = '<link rel="stylesheet" href="/assets/katex/katex.css">\n' if css_math else ''
    foot_math = ('<script defer src="/assets/katex/katex.js"></script>\n'
                 '<script defer src="/assets/katex/mhchem.js"></script>\n'
                 '<script defer src="/assets/katex/render.js"></script>\n') if css_math else ''
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
                            for i, (n, u) in enumerate(crumbs_ld)]}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{ADS}
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="小さな実験室">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}/ogp.png">
{head_math}<link rel="stylesheet" href="note.css">
<script type="application/ld+json">{ld}</script>
</head>
<body data-site="{site_id}">
{body}
{FOOTER}
{foot_math}{GOAT}
</body>
</html>
"""


FOOTER = ''


def build_note(folder, short):
    global FOOTER
    src = (ROOT / 'works' / folder / 'index.html').read_text(encoding='utf-8')
    styles = re.findall(r'<style[^>]*>(.*?)</style>', src, flags=re.S)
    scripts = re.findall(r'<script(?:\s[^>]*)?>(.*?)</script>', src, flags=re.S)
    FOOTER = re.search(r'<footer class="site-footer">.*?</footer>', src, flags=re.S).group(0)

    i = src.index('window.SITE=') + len('window.SITE=')
    site, _ = json.JSONDecoder().raw_decode(src, i)
    note_title = site['title']
    note_url = f'{BASE}/works/{folder}/'
    items_url = f'{note_url}items/'
    out = ROOT / 'works' / folder / 'items'

    # 見た目: アクセント色 + ノートの CSS + 共通フッター + 1ページ用の追記
    note_css = find_block(styles, '--rule-strong')
    h_rules = ''.join(r.replace('h3', 'h1') for r in re.findall(r'[^{}]*\bh3\b[^{}]*\{[^}]*\}', note_css))
    css = '\n'.join([find_block(styles, '--accent'), note_css, find_block(styles, '.site-footer'),
                     '/* h3 の見た目を h1 にも */' + h_rules, EXTRA_CSS])
    write(out / 'note.css', css)
    has_katex = write_katex(styles, scripts) if 'font-family:KaTeX' in src else False

    arts = {}
    for m in re.finditer(r'<article class="item".*?</article>', src, flags=re.S):
        a = m.group(0)
        arts[re.search(r' id="([^"]+)"', a).group(1)] = a

    order, unit_of = [], {}
    for u in site['units']:
        for it in u['items']:
            it['title'] = title_plain(it['title'])  # <title> や一覧では TeX を崩した文字で
            if it['id'] in arts:
                order.append(it)
                unit_of[it['id']] = u
    ids = {it['id'] for it in order}

    def fix_links(a):
        a = re.sub(r'href="#i=([^"]+)"',
                   lambda m: f'href="{m.group(1)}.html"' if m.group(1) in ids else f'href="../#i={m.group(1)}"', a)
        return re.sub(r'href="#u=([^"]+)"', r'href="./#\1"', a)

    patterns_url = f'{items_url}patterns.html'
    sitemap = [items_url, patterns_url]
    focus_of = {}  # 項目ID → 着眼点の本文（先頭の「着眼点」ラベルを除いたもの）
    for k, it in enumerate(order):
        iid, u = it['id'], unit_of[it['id']]
        siblings = [x for x in u['items'] if x['id'] in arts]
        no = next(n for n, x in enumerate(siblings, 1) if x['id'] == iid)
        a = arts[iid]
        a = re.sub(r' data-q="[^"]*"', '', a)
        a = a.replace('<span class="no"></span>', f'<span class="no" data-n="{no}"></span>', 1)
        a = re.sub(r'<h3>(.*?)</h3>', r'<h1>\1</h1>', a, count=1, flags=re.S)
        a = re.sub(r'<footer class="item-foot">.*?</footer>',
                   f'<footer class="item-foot"><a href="../#i={iid}">ノートで開いて「理解した」をつける →</a></footer>',
                   a, flags=re.S)
        a = fix_links(a)
        focus = re.search(r'<p class="focus">(.*?)</p>', a, flags=re.S)
        lead = plain(focus.group(1) if focus else a, 90)
        if focus:  # a は fix_links を通してある
            focus_of[iid] = re.sub(r'^\s*<b>着眼点</b>\s*', '', focus.group(1))
        desc = f'{it["title"]}（{u["name"]}）。{lead}'
        if len(desc) > 120:
            desc = desc[:119] + '…'

        prev_it = order[k - 1] if k > 0 else None
        next_it = order[k + 1] if k + 1 < len(order) else None
        pn = '<nav class="pn" aria-label="前後の項目">'
        if prev_it:
            pn += f'<a class="pv" href="{prev_it["id"]}.html"><small>← 前の項目</small>{esc(prev_it["title"])}</a>'
        if next_it:
            pn += f'<a class="nx" href="{next_it["id"]}.html"><small>次の項目 →</small>{esc(next_it["title"])}</a>'
        pn += '</nav>'
        sib = ''.join(
            f'<li class="cur">{esc(x["title"])}<span class="tier-mini {x["tier"]}">{TIER[x["tier"]]}</span></li>'
            if x['id'] == iid else
            f'<li><a href="{x["id"]}.html">{esc(x["title"])}</a><span class="tier-mini {x["tier"]}">{TIER[x["tier"]]}</span></li>'
            for x in siblings)
        body = f"""<header class="top"><a class="brand" href="../">{esc(note_title)}</a></header>
<main class="ip-main">
<nav class="crumbs" aria-label="現在地"><a href="/">トップ</a> › <a href="../">{esc(short)}</a> › <a href="./#{u['id']}">{esc(u['name'])}</a></nav>
{a}
{pn}
<section class="sib"><h2>「{esc(u['name'])}」の項目</h2><ol>{sib}</ol></section>
<p class="back"><a href="./">{esc(short)}の項目一覧</a> ・ <a href="patterns.html">着眼点まとめ</a> ・ <a href="../">ノート全体を開く</a>（「理解した」のチェックと進み具合はノートに保存されます）</p>
</main>"""
        url = f'{items_url}{iid}.html'
        write(out / f'{iid}.html', page(
            title=f'{it["title"]}（{u["name"]}）｜{short}', desc=desc, url=url,
            css_math=has_katex and 'class="tx"' in a, body=body, site_id=site['id'],
            crumbs_ld=[('トップ', f'{BASE}/'), (short, note_url), (f'{u["name"]}', f'{items_url}#{u["id"]}'),
                       (it['title'], url)]))
        sitemap.append(url)

    # 項目一覧と着眼点まとめは、分野（group）・単元の並べ方を共有する
    def unit_blocks(render_items):
        blocks, last_group = [], None
        for u in site['units']:
            its = [x for x in u['items'] if x['id'] in arts]
            if not its:
                continue
            if u.get('group') and u['group'] != last_group:
                blocks.append(f'<p class="grp">{esc(u["group"])}</p>')
                last_group = u['group']
            blocks.append(f'<h2 id="{u["id"]}">{u.get("icon", "")} {esc(u["name"])}</h2>{render_items(its)}')
        return ''.join(blocks)

    def tier_badge(x):
        return f'<span class="tier-mini {x["tier"]}">{TIER[x["tier"]]}</span>'

    # 項目一覧
    blocks = unit_blocks(lambda its: '<ol>' + ''.join(
        f'<li><a href="{x["id"]}.html">{esc(x["title"])}</a>{tier_badge(x)}</li>' for x in its) + '</ol>')
    lead = re.search(r'<meta name="description" content="([^"]*)"', src).group(1)
    body = f"""<header class="top"><a class="brand" href="../">{esc(note_title)}</a></header>
<main class="ip-main ilist">
<nav class="crumbs" aria-label="現在地"><a href="/">トップ</a> › <a href="../">{esc(short)}</a> › 項目一覧</nav>
<h1>{esc(short)} 項目一覧（全{len(order)}項目）</h1>
<p class="ip-note">{esc(lead)} 各項目を1ページずつ読めます。必須・差がつく・不要の3段階の線引きつき。</p>
<p class="ip-pat"><a href="patterns.html">着眼点だけを1枚で見る →</a></p>
{blocks}
<p class="back"><a href="../">ノート全体を開く</a>（オフラインで使える1ファイル版。「理解した」のチェックと進み具合を記録できます）</p>
</main>"""
    write(out / 'index.html', page(
        title=f'{short} 項目一覧（全{len(order)}項目）｜{note_title}', desc=f'{lead} 全{len(order)}項目を1ページずつ。',
        url=items_url, css_math=False, body=body, site_id=site['id'],
        crumbs_ld=[('トップ', f'{BASE}/'), (short, note_url), ('項目一覧', items_url)]))

    # 着眼点まとめ
    def pattern_items(its):
        rows = ''
        for x in its:
            f = focus_of.get(x['id'])
            rows += (f'<li class="pt"><p class="pt-h"><a href="{x["id"]}.html">{esc(x["title"])}</a>{tier_badge(x)}</p>'
                     + (f'<p class="pt-f">{f}</p>' if f else '') + '</li>')
        return f'<ul class="pt-list">{rows}</ul>'
    pat_title = f'{short}の着眼点まとめ（全{len(order)}項目）'
    pat_desc = f'{short}の全{len(order)}項目の着眼点（問題文のどこを見て、どう解き始めるか）を1ページにまとめた一覧。'
    body = f"""<header class="top"><a class="brand" href="../">{esc(note_title)}</a></header>
<main class="ip-main ilist plist">
<nav class="crumbs" aria-label="現在地"><a href="/">トップ</a> › <a href="../">{esc(short)}</a> › 着眼点まとめ</nav>
<h1>{esc(pat_title)}</h1>
<p class="ip-note">各項目の「着眼点」（問題文のどこを見て、どう解き始めるか）を、単元ごとに1ページへ並べました。項目名を押すと、その項目のページに進みます。必須・差がつく・不要の3段階つき。</p>
{unit_blocks(pattern_items)}
<p class="back"><a href="./">{esc(short)}の項目一覧</a> ・ <a href="../">ノート全体を開く</a></p>
</main>"""
    write(out / 'patterns.html', page(
        title=f'{pat_title}｜{note_title}', desc=pat_desc, url=patterns_url,
        css_math=has_katex and any('class="tx"' in f for f in focus_of.values()), body=body, site_id=site['id'],
        crumbs_ld=[('トップ', f'{BASE}/'), (short, note_url), ('着眼点まとめ', patterns_url)]))
    print(f'{folder}: {len(order)} 項目 / 記事 {len(arts)} / 数式 {"あり" if has_katex else "なし"}')
    return sitemap


def update_sitemap(urls):
    path = ROOT / 'sitemap.xml'
    s = path.read_text(encoding='utf-8')
    s = re.sub(r'\s*<url>\s*<loc>[^<]*/items/[^<]*</loc>.*?</url>', '', s, flags=re.S)
    add = ''.join(f'\n  <url>\n    <loc>{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n'
                  f'    <changefreq>monthly</changefreq>\n    <priority>{"0.6" if u.endswith("/") else "0.5"}</priority>\n  </url>'
                  for u in urls)
    s = s.replace('\n</urlset>', add + '\n</urlset>')
    path.write_text(s, encoding='utf-8')


if __name__ == '__main__':
    all_urls = []
    for folder, short in NOTES:
        all_urls += build_note(folder, short)
    update_sitemap(all_urls)
    print(f'sitemap.xml: /items/ の URL {len(all_urls)} 件')
