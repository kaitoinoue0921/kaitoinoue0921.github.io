#!/usr/bin/env python3
"""受験数学マップ（todai-math-map/app.html、1ファイルアプリ）を、1ノード1ページに分けて書き出す。

アプリは URL が1つなので、検索から個々のノードに直接入れない。
ノードごとに URL を持たせて、「確率漸化式 解き方」のような検索から着地できるようにする。

  入力: todai-math-map/app.html（触らない）。中の DATA.nodes と DATA.lessons だけ使う。
        DATA.pastexams / DATA.kakomon は入試問題の本文なので使わない（広告つきページに転載しない）。
  出力: todai-math-map/n/<ノードID>.html  各ノード（175ページ）
        todai-math-map/n/index.html        単元ごとの一覧
        todai-math-map/n/style.css         共有の見た目
        sitemap.xml                        /todai-math-map/n/ を含む <url> だけ作り直す

アプリはノード単位のURLを持たないので、「アプリで開く」は ../app.html に飛ばす。
app.html を差し替えたら、もう一度走らせる:
  python3 tools/build_mathmap_pages.py
"""
import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://kaitoinoue0921.github.io'
APP = ROOT / 'todai-math-map' / 'app.html'
OUT = ROOT / 'todai-math-map' / 'n'
TODAY = datetime.date.today().isoformat()
SITE_NAME = '受験数学マップ'

ADS = ('<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?'
       'client=ca-pub-1744436882685241" crossorigin="anonymous"></script>')
GOAT = ('<script data-goatcounter="https://kaitoinoue.goatcounter.com/count" '
        'async src="//gc.zgo.at/count.js"></script>')
FOOTER = """<footer class="site-footer">
  <ul>
    <li><a href="/">トップ</a></li>
    <li><a href="/igakubu-roadmap/">医学部受験ロードマップ</a></li>
    <li><a href="/juken/">受験・学習</a></li>
    <li><a href="/works/">作ったもの</a></li>
    <li><a href="/about/">運営者情報</a></li>
    <li><a href="/contact/">お問い合わせ</a></li>
  </ul>
  <p>運営：個人 ／ 広告とCookieについては<a href="/about/">運営者情報</a>をご覧ください</p>
</footer>"""
NOTE_LINE = ('<p class="own">解説は自作です。誤りに気づいたら '
             '<a href="/contact/">お問い合わせ（/contact/）</a>から教えてください。</p>')
FIELD_ORDER = ['中学数学', '数学I', '数学A', '数学II', '数学B', '数学III', '数学C', '東大レイヤー']

CSS = """/* 受験数学マップ 1ノード1ページ用（tools/build_mathmap_pages.py が書き出す。手で直さない） */
:root{--bg:#f6f7fa;--panel:#fff;--panel2:#eef2fb;--line:#d7dfef;--fg:#1a2436;--dim:#5c6b85;
  --accent:#173f8c;--ok:#1a8f5a;--warn:#a97b12}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--panel:#171a21;--panel2:#1a2030;--line:#2a2f3a;
  --fg:#e6e9ef;--dim:#98a0b0;--accent:#7aa5f5;--ok:#4ec9a0;--warn:#e0b34a}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.85 -apple-system,"Hiragino Sans","Noto Sans JP",
  "Yu Gothic",sans-serif;-webkit-text-size-adjust:100%}
a{color:var(--accent)}
.top{border-bottom:1px solid var(--line);background:var(--panel)}
.top a{display:block;max-width:760px;margin:0 auto;padding:12px 16px;font-weight:700;color:var(--fg);text-decoration:none}
main{max-width:760px;margin:0 auto;padding:12px 16px 56px;overflow-wrap:anywhere}
.crumbs{font-size:.8rem;color:var(--dim);margin:8px 0;line-height:1.6}
.crumbs a{color:inherit}
h1{font-size:1.6rem;line-height:1.4;margin:8px 0 6px}
h2{font-size:1.1rem;margin:30px 0 8px;padding-left:10px;border-left:3px solid var(--accent);line-height:1.5}
p{margin:0 0 12px}
.meta{font-size:.85rem;color:var(--dim);margin:0 0 14px}
.open{display:inline-block;margin:6px 0 4px;padding:9px 16px;border-radius:8px;background:var(--accent);
  color:#fff;text-decoration:none;font-size:.9rem}
@media (prefers-color-scheme:dark){.open{color:#0f1115}}
.open-note{font-size:.8rem;color:var(--dim)}
ul,ol{padding-left:1.4em;margin:0 0 12px}
li{margin:4px 0}
ol.steps{list-style:none;padding-left:0}
ol.steps li{padding-left:0}
.problem{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:0 0 10px}
details{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px 14px;margin:0 0 12px}
summary{cursor:pointer;font-weight:700;color:var(--accent)}
details ol{margin-top:8px}
.diagram{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px;margin:0 0 14px;max-width:420px}
.diagram svg{display:block;width:100%;height:auto;max-width:100%}
.links{list-style:none;padding:0;display:flex;flex-wrap:wrap;gap:6px 8px}
.links li{margin:0}
.links a{display:inline-block;padding:3px 10px;border:1px solid var(--line);border-radius:999px;background:var(--panel);
  text-decoration:none;font-size:.9rem;line-height:1.7}
.links .cur{display:inline-block;padding:3px 10px;border-radius:999px;background:var(--panel2);font-weight:700;font-size:.9rem}
.own{margin-top:32px;font-size:.85rem;color:var(--dim)}
.back{margin-top:24px;font-size:.9rem}
.grp{font-size:.85rem;color:var(--dim);margin:28px 0 -6px}
.lead{color:var(--dim);font-size:.95rem}
.site-footer{max-width:700px;margin:0 auto;padding:8px 16px 72px;text-align:center;font-size:12.5px;line-height:1.9;color:var(--dim)}
.site-footer ul{list-style:none;margin:0 0 10px;padding:0;display:flex;flex-wrap:wrap;justify-content:center;gap:6px 22px}
.site-footer a{color:var(--dim);text-decoration:none;border-bottom:1px solid var(--line);padding-bottom:2px}
.site-footer p{margin:0}
"""


def esc(s):
    return html.escape(s, quote=True)


def page(*, title, desc, url, body, crumbs):
    ld = json.dumps({
        '@context': 'https://schema.org', '@type': 'BreadcrumbList',
        'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
                            for i, (n, u) in enumerate(crumbs)]}, ensure_ascii=False)
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
<meta property="og:image" content="{BASE}/todai-math-map/ogp.png">
<link rel="stylesheet" href="style.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
{body}
{FOOTER}
{GOAT}
</body>
</html>
"""


def load():
    s = APP.read_text(encoding='utf-8')
    i = s.index('DATA = ') + len('DATA = ')
    data, _ = json.JSONDecoder().raw_decode(s, i)
    # 本文に混じったノードID（例 ma-geo-circle）を「ノード名」に置き換える
    titles = {n['id']: n['title'] for n in data['nodes']}
    pat = re.compile(r'(?<![\w-])(' + '|'.join(map(re.escape, sorted(titles, key=len, reverse=True))) + r')(?![\w-])')

    def fix(v, key=None):
        if isinstance(v, str):
            return v if key in ('id', 'nodeId', 'diagram') else pat.sub(lambda m: '「' + titles[m.group(1)] + '」', v)
        if isinstance(v, list):
            return v if key == 'prereq' else [fix(x) for x in v]
        if isinstance(v, dict):
            return {k: fix(x, k) for k, x in v.items()}
        return v
    nodes = [fix(n) for n in data['nodes']]
    lessons = [fix(x) for x in data['lessons']]
    return nodes, {x['nodeId']: x for x in lessons}


def ul(items, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<ul{c}>' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ul>'


def steps(items):
    return '<ol class="steps">' + ''.join(f'<li>{esc(x)}</li>' for x in items) + '</ol>'


def section(title, inner):
    return f'<h2>{esc(title)}</h2>\n{inner}\n' if inner else ''


def paras(text):
    return ''.join(f'<p>{esc(t)}</p>' for t in text.split('\n') if t.strip())


def main():
    nodes, lessons = load()
    byid = {n['id']: n for n in nodes}
    dependents = {n['id']: [] for n in nodes}
    for n in nodes:
        for p in n['prereq']:
            dependents[p].append(n['id'])
    by_unit = {}
    for n in nodes:
        by_unit.setdefault(n['unit'], []).append(n)

    app_url = f'{BASE}/todai-math-map/'
    list_url = f'{app_url}n/'
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'style.css').write_text(CSS, encoding='utf-8')

    def chips(ids):
        return '<ul class="links">' + ''.join(
            f'<li><a href="{i}.html">{esc(byid[i]["title"])}</a></li>' for i in ids) + '</ul>'

    urls = [list_url]
    for n in nodes:
        L = lessons[n['id']]
        flat = re.sub(r'\s+', ' ', L['core']).strip()
        desc = flat if len(flat) <= 110 else flat[:109] + '…'
        title = f'{n["title"]}（{n["unit"]}）｜{SITE_NAME}'
        url = f'{list_url}{n["id"]}.html'

        parts = []
        if L.get('core'):
            parts.append(section('要点', paras(L['core'])))
        if L.get('diagram'):
            parts.append(f'<div class="diagram" role="img" aria-label="{esc(n["title"])}の図">{L["diagram"]}</div>\n')
        parts.append(section('こんなときに使う', ul(L.get('trigger') or [])) if L.get('trigger') else '')
        parts.append(section('手順', steps(L['procedure'])) if L.get('procedure') else '')
        w = L.get('worked') or {}
        if w.get('problem'):
            inner = f'<div class="problem">{esc(w["problem"])}</div>'
            if w.get('solution'):
                inner += f'<details><summary>解答</summary>{steps(w["solution"])}</details>'
            parts.append(section('例題', inner))
        parts.append(section('別解・ほかの見方', ul(L['variants'])) if L.get('variants') else '')
        pit = list(L.get('pitfalls') or [])
        if n.get('trap') and n['trap'] not in pit:
            pit.append(n['trap'])
        parts.append(section('落とし穴', ul(pit)) if pit else '')
        parts.append(section('なぜ大事か', paras(n['why'])) if n.get('why') else '')
        parts.append(section('東大での出方', paras(L['todaiUse'])) if L.get('todaiUse') else '')
        parts.append(section('確認問題', ul(L['check'])) if L.get('check') else '')
        parts.append(section('発展', paras(L['stretch'])) if L.get('stretch') else '')
        if n['prereq']:
            parts.append(section('前提になるノード', chips(n['prereq'])))
        if dependents[n['id']]:
            parts.append(section('このノードを前提にするノード', chips(dependents[n['id']])))
        same = ''.join(
            f'<li><span class="cur">{esc(m["title"])}</span></li>' if m['id'] == n['id'] else
            f'<li><a href="{m["id"]}.html">{esc(m["title"])}</a></li>' for m in by_unit[n['unit']])
        parts.append(section(f'「{n["unit"]}」のノード', f'<ul class="links">{same}</ul>'))

        stars = '★' * n['todai'] + '☆' * (5 - n['todai']) if 1 <= n['todai'] <= 5 else ''
        meta = f'{esc(n["field"])} ／ {esc(n["unit"])}' + (f' ／ 東大での重要度 {stars}' if stars else '')
        body = f"""<header class="top"><a href="../">{SITE_NAME}</a></header>
<main>
<nav class="crumbs" aria-label="現在地"><a href="/">トップ</a> › <a href="../">{SITE_NAME}</a> › <a href="./">ノード一覧</a> › {esc(n['title'])}</nav>
<h1>{esc(n['title'])}</h1>
<p class="meta">{meta}</p>
<p><a class="open" href="../app.html">アプリで開く →</a><br><span class="open-note">進み具合を記録できるアプリ版です（ノード単位の直リンクはありません）</span></p>
{''.join(parts)}{NOTE_LINE}
<p class="back"><a href="./">ノード一覧</a> ・ <a href="../">{SITE_NAME}について</a></p>
</main>"""
        (OUT / f'{n["id"]}.html').write_text(page(
            title=title, desc=desc, url=url, body=body,
            crumbs=[('トップ', f'{BASE}/'), (SITE_NAME, app_url), ('ノード一覧', list_url), (n['title'], url)]),
            encoding='utf-8')
        urls.append(url)

    # 一覧: 分野（field）→ 単元（unit）の順
    blocks = []
    fields = sorted({n['field'] for n in nodes}, key=lambda f: FIELD_ORDER.index(f) if f in FIELD_ORDER else 99)
    for f in fields:
        blocks.append(f'<p class="grp">{esc(f)}</p>')
        units = []
        for n in nodes:
            if n['field'] == f and n['unit'] not in units:
                units.append(n['unit'])
        for u in units:
            items = [m for m in by_unit[u] if m['field'] == f]
            blocks.append(f'<h2>{esc(u)}</h2><ul class="links">' + ''.join(
                f'<li><a href="{m["id"]}.html">{esc(m["title"])}</a></li>' for m in items) + '</ul>')
    lead = 'つながり図で構造化した受験数学の全ノードを、1ノード1ページで読めます。中学数学から東大数学まで。'
    title = f'ノード一覧（全{len(nodes)}項目）｜{SITE_NAME}'
    body = f"""<header class="top"><a href="../">{SITE_NAME}</a></header>
<main>
<nav class="crumbs" aria-label="現在地"><a href="/">トップ</a> › <a href="../">{SITE_NAME}</a> › ノード一覧</nav>
<h1>{SITE_NAME} ノード一覧（全{len(nodes)}項目）</h1>
<p class="lead">{esc(lead)}各ページに、要点・手順・例題・落とし穴・東大での出方を載せています。</p>
{''.join(blocks)}
{NOTE_LINE}
<p class="back"><a href="../app.html">アプリを開く</a> ・ <a href="../">{SITE_NAME}について</a></p>
</main>"""
    (OUT / 'index.html').write_text(page(
        title=title, desc=f'{lead}全{len(nodes)}項目。', url=list_url, body=body,
        crumbs=[('トップ', f'{BASE}/'), (SITE_NAME, app_url), ('ノード一覧', list_url)]), encoding='utf-8')

    # sitemap.xml: /todai-math-map/n/ を含む <url> だけ作り直す
    path = ROOT / 'sitemap.xml'
    s = path.read_text(encoding='utf-8')
    s = re.sub(r'\s*<url>\s*<loc>[^<]*/todai-math-map/n/[^<]*</loc>.*?</url>', '', s, flags=re.S)
    add = ''.join(f'\n  <url>\n    <loc>{u}</loc>\n    <lastmod>{TODAY}</lastmod>\n'
                  f'    <changefreq>monthly</changefreq>\n    <priority>{"0.6" if u.endswith("/") else "0.5"}</priority>\n  </url>'
                  for u in urls)
    s = s.replace('\n</urlset>', add + '\n</urlset>')
    path.write_text(s, encoding='utf-8')
    print(f'{len(nodes)} ノード + 一覧 = {len(urls)} ページ / sitemap.xml に {len(urls)} 件')


if __name__ == '__main__':
    main()
