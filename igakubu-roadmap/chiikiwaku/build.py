#!/usr/bin/env python3
"""地域枠・修学資金くらべの静的ビルド。 python3 chiikiwaku/build.py

入力: chiikiwaku/prefectures.json
出力: chiikiwaku/site/ (index.html, pref/<id>.html, sitemap.xml, robots.txt, assets/style.css)
公開先とブランド名は未定。環境変数 BASE_URL と SITE で切り替える。
"""
import os, json, html, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "site")
BASE_URL = os.environ.get("BASE_URL", "https://kaitoinoue0921.github.io/chiikiwaku").rstrip("/")
SITE = os.environ.get("SITE", "地域枠・修学資金くらべ")
PARENT = ("医学部受験ロードマップ", "https://kaitoinoue0921.github.io/igakubu-roadmap/")
esc = html.escape

DATA = json.load(open(os.path.join(HERE, "prefectures.json"), encoding="utf-8"))
CHECKED = max(p["checked"] for p in DATA)

def man(y):
    return f"月{y // 10000}万円" if y % 10000 == 0 else f"月{y / 10000:g}万円"

def monthly(p):
    return man(p["monthly_yen"]) if p["monthly_yen"] else "月額は一定でない"

def years(p):
    return f"{p['obligation_years']}年" if p["obligation_years"] else "要確認"

def badge(p):
    cls = "ok" if p["status"].startswith("確認済み") and not p["unconfirmed"] else "warn"
    return f'<span class="st {cls}">{esc(p["status"])}</span>'

def page(path, title, desc, body, depth):
    up = "../" * depth
    url = f"{BASE_URL}/{path}"
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url,
                     "inLanguage": "ja", "isPartOf": {"@type": "WebSite", "name": SITE, "url": BASE_URL + "/"}},
                    ensure_ascii=False)
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@600;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{up}assets/style.css">
<style>.st{{display:inline-block;font-size:.78rem;padding:1px 8px;border-radius:999px}}.st.ok{{background:var(--ok-soft);color:var(--ok)}}.st.warn{{background:var(--gold-soft);color:var(--gold)}}.pl{{display:grid;grid-template-columns:8em 1fr;gap:4px 14px;margin:12px 0}}.pl dt{{font-weight:700;color:var(--ink-soft)}}.pl dd{{margin:0}}@media(max-width:520px){{.pl{{grid-template-columns:1fr}}}}</style>
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="site-head"><div class="wrap">
  <a class="brand" href="{up}index.html">{esc(SITE)}</a>
  <nav class="nav"><a href="{up}index.html#table">比較表</a><a href="{up}index.html#pref">県別</a><a href="{PARENT[1]}">{esc(PARENT[0])}</a></nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="wrap note">
<p>数字は各県・大学の公開資料から拾ったもので、最終確認日は{CHECKED}です。出願の前に、必ず県と大学の最新の要項で確かめてください。</p>
<p><a href="{PARENT[1]}">{esc(PARENT[0])}</a>もあわせてどうぞ。</p>
</footer>
</body>
</html>
"""

def pref_page(p):
    unconf = ("<ul>" + "".join(f"<li>{esc(u)}</li>" for u in p["unconfirmed"]) + "</ul>") if p["unconfirmed"] \
        else "<p>いまのところ、未確認として残している項目はありません。</p>"
    src = "".join(f'<li><a href="{esc(u)}" rel="noopener" target="_blank">{esc(u)}</a></li>' for u in p["sources"])
    body = f"""<h1>{esc(p["pref"])}の地域枠と修学資金</h1>
<p class="lead">{esc(p["univ"])}。{badge(p)}</p>
<dl class="pl">
<dt>定員</dt><dd>{esc(p["capacity"])}</dd>
<dt>貸与額</dt><dd>{esc(p["loan"])}</dd>
<dt>義務年限と勤務先</dt><dd>{esc(p["obligation"])}</dd>
<dt>資料の年度</dt><dd>{esc(p["fiscal_year"])}</dd>
<dt>最終確認日</dt><dd>{esc(p["checked"])}</dd>
</dl>
<h2>まだ確認できていないこと</h2>
{unconf}
<h2>出典</h2>
<ul class="src">{src}</ul>
<p><a href="../index.html#table">全県の比較表にもどる</a></p>"""
    return page(f"pref/{p['id']}.html", f"{p['pref']}の地域枠と修学資金｜{SITE}",
                f"{p['pref']}（{p['univ']}）の地域枠の定員、貸与額、義務年限。出典と確認日つき。", body, 1)

def index_page():
    rows = ""
    for p in DATA:
        rows += (f'<tr><td><a href="pref/{p["id"]}.html">{esc(p["pref"])}</a><br>{esc(p["univ"])}</td>'
                 f'<td>{esc(monthly(p))}</td><td>{esc(years(p))}</td><td>{esc(p["capacity"])}</td><td>{badge(p)}</td></tr>\n')
    known = [p for p in DATA if p["monthly_yen"]]
    lo_y = min(p["monthly_yen"] for p in known); hi_y = max(p["monthly_yen"] for p in known)
    lo_n = "、".join(p["pref"] for p in known if p["monthly_yen"] == lo_y)
    hi_n = "、".join(p["pref"] for p in known if p["monthly_yen"] == hi_y)
    nine = sum(1 for p in DATA if p["obligation_years"] == 9)
    unconf = sum(1 for p in DATA if p["unconfirmed"])
    cards = "".join(f'<li><a href="pref/{p["id"]}.html">{esc(p["pref"])}</a>　{esc(p["univ"])}</li>' for p in DATA)
    body = f"""<h1>{esc(SITE)}</h1>
<p class="lead">地域枠は、入学時から県が学費や生活費を貸し、卒業後に県が指定する病院で決まった年数働くと返さなくてよくなる仕組みです。{len(DATA)}県を、貸与額・義務年限・定員で並べました。確認できた数字と、まだ確認できていない数字は分けて書いています。</p>
<div class="judge"><p>{len(DATA)}県のうち{nine}県で義務年限は9年です。生活費の月額で比べられる{len(known)}県では、最も低いのが{esc(lo_n)}の{esc(man(lo_y))}、最も高いのが{esc(hi_n)}の{esc(man(hi_y))}です。ただし{unconf}県には未確認の項目が残っています。借りる額より、9年間どこで働くかを先に見てください。</p></div>
<h2 id="table">比較表</h2>
<div class="tscroll"><table class="t">
<tr><th>県と大学</th><th>生活費の貸与</th><th>義務年限</th><th>定員</th><th>確認の状態</th></tr>
{rows}</table></div>
<p class="note">月額は生活費の貸与のみで、入学料や授業料は含みません。県ごとの詳しい内訳は各県のページにあります。</p>
<h2 id="pref">県別のページ</h2>
<ul>{cards}</ul>"""
    return page("index.html", f"{SITE}｜九州の医学部地域枠を比べる",
                "九州各県の医学部地域枠と修学資金を、貸与額・義務年限・定員で比較。全行に出典と確認日つき。", body, 0)

def write(rel, s):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(s)

def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(os.path.join(OUT, "assets"))
    shutil.copy(os.path.join(HERE, "..", "assets", "style.css"), os.path.join(OUT, "assets", "style.css"))
    write("index.html", index_page())
    urls = [""]
    for p in DATA:
        write(f"pref/{p['id']}.html", pref_page(p)); urls.append(f"pref/{p['id']}.html")
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sm += "".join(f"<url><loc>{BASE_URL}/{u}</loc></url>\n" for u in urls) + "</urlset>\n"
    write("sitemap.xml", sm)
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    print(f"{len(DATA)}県 → {len(urls)}ページ を {OUT} に出力")

if __name__ == "__main__":
    main()
