#!/usr/bin/env python3
"""印刷用「つまずきパターン集」（試作）を作る。

高校ノート4冊の各項目にある「注意」欄（<div class="box warn">）だけを、
分野 → 単元 → 項目の順に集めて、科目ごとに1枚の印刷向けページにする。
着眼点（focus 欄）は載せない。

  入力: works/<ノート>/index.html（触らない）
  出力: works/tsumazuki/{math,chem,physics,eng-grammar}.html  科目ごとのページ
        works/tsumazuki/index.html                           入口と試作の説明
        works/tsumazuki/style.css                            見た目（画面・印刷）
  数式の描画は assets/katex/（build_note_pages.py が作ったもの）を使う。
  試作なので noindex、AdSense なし、sitemap.xml に足さない、他ページからリンクしない。

何度でも作り直せる:
  python3 tools/build_tsumazuki.py
"""
import html
import json
import re
from pathlib import Path

from tex_title import title_plain

ROOT = Path(__file__).resolve().parent.parent
BASE = 'https://kaitoinoue0921.github.io'
OUT = ROOT / 'works' / 'tsumazuki'
SUBJECTS = [  # (出力名, ノートのフォルダ, 短い名前)
    ('math', 'math-notes', '高校数学'),
    ('chem', 'chem-notes', '高校化学'),
    ('physics', 'physics-notes', '高校物理'),
    ('eng-grammar', 'eng-grammar-notes', '英文法'),
]
TIER = {'must': '必須', 'core': '差がつく', 'skip': '不要'}
GOAT = ('<script data-goatcounter="https://kaitoinoue.goatcounter.com/count" '
        'async src="//gc.zgo.at/count.js"></script>')
ACCENT = {'math': '#2f5d8a', 'chem': '#7a4a9a', 'physics': '#b5651d', 'eng-grammar': '#a6392a'}

CSS = """/* つまずきパターン集（試作）。配色トークンは works/*-notes/items/note.css と同じ。 */
:root{
  --bg:#f4f4ef;--surface:#fff;--surface-2:#ecece4;--ink:#22261f;--ink-soft:#5a6052;
  --rule:#d9dacd;--rule-strong:#b9bcaa;
  --must:#a6392a;--must-soft:#f4ded9;--core:#9a7425;--core-soft:#f1e6cd;--skip:#6b7280;--skip-soft:#e6e8e3;
  --accent:#2f5d8a;--link:var(--accent);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#171a15;--surface:#1f231c;--surface-2:#262b21;--ink:#e9ece2;--ink-soft:#a7ad9c;
  --rule:#343a2d;--rule-strong:#454c3a;--must:#e08464;--must-soft:#3a251d;--core:#d9b465;--core-soft:#33291a;
  --skip:#9aa192;--skip-soft:#262b21;--link:color-mix(in srgb,var(--accent) 55%,#fff)}}
body[data-s="math"]{--accent:#2f5d8a}
body[data-s="chem"]{--accent:#7a4a9a}
body[data-s="physics"]{--accent:#b5651d}
body[data-s="eng-grammar"]{--accent:#a6392a}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);line-height:1.85;font-size:16px;
  font-family:-apple-system,"Hiragino Sans","Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif}
a{color:var(--link)}
h1,h2{line-height:1.4;font-family:"Hiragino Mincho ProN","Yu Mincho",serif}
.top{display:flex;align-items:center;padding:8px 16px;background:var(--surface);border-bottom:1px solid var(--rule)}
.brand{font-weight:800;font-family:"Hiragino Mincho ProN","Yu Mincho",serif;color:var(--ink);text-decoration:none;font-size:1.02rem}
.main{max-width:840px;margin:0 auto;padding:12px 16px 56px;overflow-wrap:anywhere}
.main h1{font-size:1.5rem;margin:18px 0 6px}
.lead{margin:0 0 6px}
.count{margin:0 0 6px;color:var(--ink-soft);font-size:.9rem}
.proto{margin:6px 0 14px;padding:8px 12px;border-left:4px solid var(--accent);background:var(--surface);font-size:.88rem;color:var(--ink-soft)}
.grp{font-size:.8rem;color:var(--ink-soft);margin:26px 0 -6px;letter-spacing:.06em;break-after:avoid}
.main h2{font-size:1.1rem;margin:20px 0 4px;padding-bottom:2px;border-bottom:2px solid var(--accent);break-after:avoid}
.ts-list{list-style:none;padding:0;margin:0}
.ts{padding:10px 0}
.ts + .ts{border-top:1px solid var(--rule)}
.ts-h{margin:0;line-height:1.5}
.ts-h a{font-weight:700}
.ts-w{margin:4px 0 0;font-size:.95rem;line-height:1.75;padding-left:.8em;border-left:3px solid var(--must)}
.ts-w + .ts-w{margin-top:6px}
.tier-mini{font-size:.7rem;padding:0 6px;border-radius:4px;margin-left:6px;vertical-align:1px;white-space:nowrap}
.tier-mini.must{background:var(--must-soft);color:var(--must)}
.tier-mini.core{background:var(--core-soft);color:var(--core)}
.tier-mini.skip{background:var(--skip-soft);color:var(--skip)}
.cards{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));margin:18px 0}
.card{display:block;background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--ink)}
.card:hover{border-color:var(--accent)}
.card b{display:block}.card span{font-size:.85rem;color:var(--ink-soft);display:block;margin-top:2px}
.back{margin:28px 0 0;font-size:.9rem}
.katex-display{overflow-x:auto;overflow-y:hidden;max-width:100%}
.site-footer{max-width:700px;margin:0 auto;padding:8px 24px 72px;text-align:center;font-size:12.5px;line-height:1.9;color:var(--ink-soft)}
.site-footer ul{list-style:none;margin:0 0 10px;padding:0;display:flex;flex-wrap:wrap;justify-content:center;gap:6px 22px}
.site-footer a{color:var(--ink-soft);text-decoration:none;border-bottom:1px solid var(--rule-strong);padding-bottom:2px}
.site-footer p{margin:0}
/* 印刷: A4・2段組。ダークモードでも白地・黒字にする */
@media print{
  :root,:root:not([data-theme="light"]){--bg:#fff;--surface:#fff;--surface-2:#f2f2f2;--ink:#000;--ink-soft:#333;
    --rule:#bbb;--rule-strong:#888;--must:#a6392a;--must-soft:#f4ded9;--core:#7a5a10;--core-soft:#f1e6cd;--skip:#444;--skip-soft:#eee;--link:#000}
  @page{size:A4;margin:12mm}
  html,body{background:#fff!important;color:#000!important}
  body{font-size:10.5pt;line-height:1.6}
  .top,.site-footer,.back,.proto{display:none!important}
  .main{max-width:none;padding:0}
  .main h1{font-size:15pt;margin:0 0 2mm}
  .lead,.count{font-size:9pt;margin:0 0 2mm}
  .cols{column-count:2;column-gap:10mm}
  .main h2{font-size:11.5pt;margin:4mm 0 1mm}
  .grp{margin:4mm 0 0}
  .ts{padding:2mm 0;break-inside:avoid}
  .ts-h{font-size:10.5pt}
  .ts-h a{text-decoration:none;color:#000}
  .ts-w{font-size:10pt;line-height:1.55}
}
"""


def esc(s):
    return html.escape(s, quote=True)


def read_note(folder):
    src = (ROOT / 'works' / folder / 'index.html').read_text(encoding='utf-8')
    i = src.index('window.SITE=') + len('window.SITE=')
    site, _ = json.JSONDecoder().raw_decode(src, i)
    footer = re.search(r'<footer class="site-footer">.*?</footer>', src, flags=re.S).group(0)
    warns = {}
    for m in re.finditer(r'<article class="item".*?</article>', src, flags=re.S):
        a = m.group(0)
        iid = re.search(r' id="([^"]+)"', a).group(1)
        ws = []
        for w in re.findall(r'<div class="box warn">(.*?)</div>', a, flags=re.S):
            w = re.sub(r'^\s*<b[^>]*>注意</b>\s*', '', w)
            if w.strip():
                ws.append(w.strip())
        warns[iid] = ws
    return site, footer, warns


def page(*, title, desc, url, body, footer, math, sid):
    head_math = '<link rel="stylesheet" href="/assets/katex/katex.css">\n' if math else ''
    foot_math = ('<script defer src="/assets/katex/katex.js"></script>\n'
                 '<script defer src="/assets/katex/mhchem.js"></script>\n'
                 '<script defer src="/assets/katex/render.js"></script>\n') if math else ''
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,follow">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
{head_math}<link rel="stylesheet" href="style.css">
</head>
<body data-s="{sid}">
<header class="top"><a class="brand" href="./">つまずきパターン集（試作）</a></header>
<main class="main">
{body}
</main>
{footer}
{foot_math}{GOAT}
</body>
</html>
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'style.css').write_text(CSS, encoding='utf-8')
    footer, cards = '', []
    for sid, folder, short in SUBJECTS:
        site, footer, warns = read_note(folder)
        n_items = n_warns = 0
        blocks, last_group, has_tx = [], None, False
        for u in site['units']:
            rows = ''
            for it in u['items']:
                ws = warns.get(it['id'])
                if not ws:
                    continue
                n_items += 1
                n_warns += len(ws)
                has_tx = has_tx or any('class="tx"' in w for w in ws)
                tier = it['tier']
                rows += (f'<li class="ts"><p class="ts-h"><a href="/works/{folder}/items/{it["id"]}.html">'
                         f'{esc(title_plain(it["title"]))}</a>'
                         f'<span class="tier-mini {tier}">{TIER[tier]}</span></p>'
                         + ''.join(f'<p class="ts-w">{w}</p>' for w in ws) + '</li>')
            if not rows:
                continue
            if u.get('group') and u['group'] != last_group:
                blocks.append(f'<p class="grp">{esc(u["group"])}</p>')
                last_group = u['group']
            blocks.append(f'<h2>{u.get("icon", "")} {esc(u["name"])}</h2><ul class="ts-list">{rows}</ul>')
        title = f'つまずきパターン集（試作）｜{short}'
        body = f"""<h1>{esc(short)}　つまずきパターン集</h1>
<p class="count">{n_items}項目・{n_warns}件</p>
<p class="lead">ノートの各項目の「注意」欄を、単元ごとに集めたものです。解き始め方は<a href="/works/{folder}/items/patterns.html">着眼点まとめ</a>にあります。</p>
<p class="proto">試作版です。印刷するときは、ブラウザの印刷でA4・余白は標準にしてください。</p>
<div class="cols">{''.join(blocks)}</div>
<p class="back"><a href="./">つまずきパターン集（試作）の入口へ</a></p>"""
        page_html = page(title=title, desc=f'{short}ノートの「注意」欄を単元ごとに集めた印刷用ページ（試作）。',
                         url=f'{BASE}/works/tsumazuki/{sid}.html', body=body, footer=footer,
                         math=has_tx, sid=sid)
        (OUT / f'{sid}.html').write_text(page_html, encoding='utf-8')
        cards.append(f'<a class="card" href="{sid}.html"><b>{esc(short)}</b><span>{n_items}項目・{n_warns}件</span></a>')
        print(f'{sid}: {n_items} 項目 / {n_warns} 件')

    body = f"""<h1>つまずきパターン集（試作）</h1>
<p class="lead">高校ノートの各項目にある「注意」欄（間違えやすい点）を、科目ごとに1枚へ集めた、印刷用のページです。</p>
<p class="lead"><b>試作版です。</b>いまはノートの注意欄から機械的に作っていて、実際の生徒の質問をもとにした並べ替えはこれからです。</p>
<div class="cards">{''.join(cards)}</div>
<p class="count">並びは、分野、単元、項目の順です。項目名を押すと、ノートのその項目のページに進みます。A4・2段組で印刷できます。</p>"""
    (OUT / 'index.html').write_text(page(
        title='つまずきパターン集（試作）', desc='高校ノートの「注意」欄を科目ごとに集めた印刷用ページの試作。',
        url=f'{BASE}/works/tsumazuki/', body=body, footer=footer, math=False, sid=''), encoding='utf-8')


if __name__ == '__main__':
    main()
