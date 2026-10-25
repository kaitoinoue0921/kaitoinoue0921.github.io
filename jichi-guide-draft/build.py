#!/usr/bin/env python3
"""自治医大まわりの手帖の静的ビルド。 python3 build.py
入力: data/study.json（勉強スポット）, data/eat.json（食べるところ）
出力: index.html, study/index.html, eat/index.html, about/index.html, sitemap.xml, robots.txt
"""
import json, html, os
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.environ.get("BASE_URL", "https://kaitoinoue0921.github.io/jichi-guide").rstrip("/")
SITE = "自治医大まわりの手帖"
MAIN = "https://kaitoinoue0921.github.io"
esc = html.escape
STUDY = json.load(open(os.path.join(HERE, "data/study.json"), encoding="utf-8"))
EAT = json.load(open(os.path.join(HERE, "data/eat.json"), encoding="utf-8"))
UPDATED = "2026-10-25"

FOOT = f"""<style>.site-footer a{{border-bottom:1px solid var(--rule);text-decoration:none}}</style>
<footer class="site-footer"><ul>
<li><a href="{MAIN}/">小さな実験室（親サイト）</a></li><li><a href="{MAIN}/igakubu-roadmap/">医学部受験ロードマップ</a></li>
<li><a href="{MAIN}/study-map/">スタディスポットMAP</a></li><li><a href="{MAIN}/about/">運営者情報</a></li>
<li><a href="{MAIN}/privacy/">プライバシーポリシー</a></li><li><a href="{MAIN}/contact/">お問い合わせ</a></li></ul>
<p>運営：個人（自治医科大学の医学生） ／ 公式のサイトではありません</p></footer>
<script data-goatcounter="https://kaitoinoue.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>"""

def page(path, title, desc, body, depth, noindex=False):
    up = "../" * depth
    url = f"{BASE}/{path}".replace("index.html", "")
    robots = '<meta name="robots" content="noindex">\n' if noindex else ""
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-1744436882685241" crossorigin="anonymous"></script>
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{robots}<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}"><meta property="og:type" content="website"><meta property="og:locale" content="ja_JP"><meta property="og:url" content="{url}">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@600;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<header class="head"><div class="wrap"><a class="brand" href="{up}index.html">{SITE}</a>
<nav class="nav"><a href="{up}study/index.html">勉強する</a><a href="{up}eat/index.html">食べる</a><a href="{up}about/index.html">このサイトについて</a></nav></div></header>
<main class="wrap">
{body}
</main>
{FOOT}
</body>
</html>
"""

def facilities(f):
    names = {"wifi": "Wi-Fi", "aircon": "冷暖房", "water": "飲み水", "power": "電源"}
    return "、".join(names[k] for k in (f or {}) if f[k] and k in names) or "要確認"

def spot_html(p):
    maps = f"https://www.google.com/maps/search/?api=1&query={p['lat']},{p['lng']}"
    unconf = "要確認" in (p.get("closed") or "") or "未確認" in (p.get("hoursWd") or "")
    tag = '<span class="tag warn">営業時間などに未確認あり</span>' if unconf else ""
    visited = '<span class="tag">筆者が行った</span>' if p.get("visited") else ""
    hours = p["hoursWd"] if p["hoursWd"] == p["hoursWe"] else f"平日 {p['hoursWd']} ／ 土日 {p['hoursWe']}"
    return f"""<article class="spot" data-cat="{esc(p['category'])}">
<h3>{esc(p['name'])}</h3>
<p><span class="tag">{esc(p['category'])}</span>{visited}{tag}<span class="note">直線で約{p['km']:g}km</span></p>
<dl><dt>営業時間</dt><dd>{esc(hours)}</dd><dt>休み</dt><dd>{esc(p['closed'])}</dd><dt>料金</dt><dd>{esc(p['fee'])}</dd><dt>設備</dt><dd>{esc(facilities(p.get('facilities')))}</dd><dt>住所</dt><dd>{esc(p['address'])}（<a href="{maps}" rel="noopener" target="_blank">地図</a>）</dd></dl>
<p>{esc(p['note'])}</p></article>"""

def study_page():
    groups = [("自治医大のすぐそば（直線で3km以内）", 0, 3), ("少し歩く・自転車で行ける（3〜10km）", 3, 10), ("車があれば（10〜20km）", 10, 21)]
    cats = sorted({p["category"] for p in STUDY})
    btn = '<button type="button" aria-pressed="true" data-c="">すべて</button>' + "".join(f'<button type="button" aria-pressed="false" data-c="{esc(c)}">{esc(c)}</button>' for c in cats)
    sec = ""
    for title, lo, hi in groups:
        items = [p for p in STUDY if lo <= p["km"] < hi]
        if items:
            sec += f"<h2>{title}　<small class='note'>{len(items)}件</small></h2>\n" + "\n".join(spot_html(p) for p in items) + "\n"
    n_near = sum(1 for p in STUDY if p["km"] < 3)
    body = f"""<h1>自治医大まわりの勉強する場所</h1>
<p class="lead">図書館、カフェ、ファミレス、公民館の学習スペースなど、自治医科大学から直線で20km以内の{len(STUDY)}か所を、近い順にまとめました。大学のすぐそばには{n_near}か所あります。</p>
<div class="box"><p>営業時間や休みは、各施設の公開情報から拾ったものです。「要確認」「未確認」と書いてあるものは、まだ確かめていません。行く前に公式の情報で見てください。「筆者が行った」の印がつくのは、実際に行って確かめた場所だけです。いまは印のついた場所はありません。距離は直線なので、実際の道のりはもっと長くなります。</p></div>
<div class="filters" id="f">{btn}</div>
{sec}
<p class="note">地図で探したい人は、親サイトの<a href="{MAIN}/study-map/">スタディスポットMAP</a>で全国の場所を見られます。最終更新：{UPDATED}</p>
<script>
(function(){{var b=document.querySelectorAll('#f button'),s=document.querySelectorAll('.spot');
b.forEach(function(x){{x.onclick=function(){{b.forEach(function(y){{y.setAttribute('aria-pressed',y===x)}});s.forEach(function(e){{e.hidden=x.dataset.c&&e.dataset.cat!==x.dataset.c}})}}}})}})();
</script>"""
    return page("study/index.html", f"自治医大まわりの勉強する場所｜{SITE}", f"自治医科大学から近い図書館・カフェ・ファミレス・公民館など{len(STUDY)}か所を、距離・営業時間・設備でまとめた一覧。確認できていない項目は未確認と書いている。", body, 1)

def eat_page():
    if EAT:
        cards = "".join(f"""<article class="spot"><h3>{esc(e['name'])}</h3><p><span class="tag">{esc(e.get('genre',''))}</span><span class="note">{esc(e.get('area',''))}</span></p>
<dl><dt>値段</dt><dd>{esc(e.get('price','要確認'))}</dd><dt>向いている時</dt><dd>{esc(e.get('scene',''))}</dd><dt>行った日</dt><dd>{esc(e.get('visited',''))}</dd></dl><p>{esc(e.get('comment',''))}</p></article>""" for e in EAT)
        body = f"""<h1>自治医大まわりの食べる場所</h1><p class="lead">実際に行った店だけを載せています。</p>{cards}"""
        return page("eat/index.html", f"自治医大まわりの食べる場所｜{SITE}", "自治医科大学の近くで、実際に行って書いた店の紹介。", body, 1)
    body = """<h1>自治医大まわりの食べる場所</h1>
<p class="lead">ここは、実際に行った店だけを載せるページです。まだ1軒も書いていません。</p>
<div class="box"><p>店のおすすめは、行った人にしか書けません。ネットの口コミを集めて並べても、役に立つものにならないので、書けるようになってから足します。</p></div>
<p>載せるときは、次の項目で書きます。</p>
<ul><li>店名と場所（駅からの行き方）</li><li>ジャンルと値段の目安</li><li>どんなときに向いているか（試験前の夜、実習のあと、ひとりで、少人数で、など）</li><li>行った日と、そのときの感想</li></ul>"""
    return page("eat/index.html", f"自治医大まわりの食べる場所｜{SITE}", "自治医科大学の近くで、実際に行って書いた店の紹介ページ。準備中。", body, 1, noindex=True)

def index_page():
    near = [p for p in STUDY if p["km"] < 3][:4]
    nearli = "".join(f"<li>{esc(p['name'])}（{esc(p['category'])}、直線で約{p['km']:g}km）</li>" for p in near)
    body = f"""<h1>{SITE}</h1>
<p class="lead">自治医科大学の学生が、学内の勉強に疲れたときに行ける場所と、ごはんを食べられる場所を書いていく読み物です。公式のサイトではなく、個人が作っています。</p>
<div class="cards">
<div class="card big"><h3><a class="t" href="study/index.html">勉強する場所 →</a></h3><p class="note">大学から20km以内の{len(STUDY)}か所。図書館、カフェ、ファミレス、公民館。</p><p class="note">大学のすぐそば：</p><ul class="note">{nearli}</ul></div>
<div class="card big"><h3><a class="t" href="eat/index.html">食べる場所 →</a></h3><p class="note">実際に行った店だけを書きます。いまは準備中です。</p></div>
</div>
<h2>このサイトの方針</h2>
<ul><li>確かめていない数字は、確かめていないと書く。</li><li>おすすめは、行った人が書く。</li><li>広告が入ることがあります。広告やリンクの有無で、書く内容は変えません。</li></ul>
<p class="note">最終更新：{UPDATED}</p>"""
    return page("index.html", f"{SITE}｜勉強する場所・食べる場所", "自治医科大学の学生向けに、近くで勉強できる場所と食べる場所をまとめている個人の読み物サイト。", body, 0)

def about_page():
    body = f"""<h1>このサイトについて</h1>
<p>自治医科大学の医学生が、個人で運営しています。大学や関係団体の公式サイトではありません。</p>
<h2>情報について</h2>
<p>勉強する場所の情報は、各施設の公開情報（公式サイトや Google の掲載情報）から手で拾ったものです。確かめられていない項目には、そう書いています。間違いを見つけたら<a href="{MAIN}/contact/">お問い合わせ</a>から教えてください。確かめて直します。</p>
<h2>広告について</h2>
<p>広告（Google AdSense）を表示しています。アクセス解析は GoatCounter です。くわしくは<a href="{MAIN}/privacy/">プライバシーポリシー</a>と<a href="{MAIN}/about/">運営者情報</a>にあります。</p>
<h2>親サイト</h2>
<p><a href="{MAIN}/">小さな実験室</a>の中で作っているものの1つです。</p>"""
    return page("about/index.html", f"このサイトについて｜{SITE}", f"{SITE}の運営者、情報の集め方、広告について。", body, 1)

def write(rel, s):
    p = os.path.join(HERE, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w", encoding="utf-8").write(s)

write("index.html", index_page()); write("study/index.html", study_page()); write("eat/index.html", eat_page()); write("about/index.html", about_page())
urls = ["", "study/", "about/"] + (["eat/"] if EAT else [])
write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{BASE}/{u}</loc><lastmod>{UPDATED}</lastmod></url>\n" for u in urls) + "</urlset>\n")
write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
print("built", len(STUDY), "spots,", len(EAT), "eat")
