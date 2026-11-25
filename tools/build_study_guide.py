#!/usr/bin/env python3
"""Generate the ad-free exam guide from its original lesson data."""
import json
import re
from collections import Counter
from html import escape
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'juken/guide'
BASE = '/juken/guide/'
SITE = 'https://kaitoinoue0921.github.io'
LEVEL = {'foundation': '基本', 'standard': '標準', 'mixed': '融合'}
GROUPS = (
    ('数学', 'Σ', {'math': '数学'}),
    ('国語', '文', {'japanese': '国語'}),
    ('外国語', 'Aa', {'english': '英語', 'german': 'ドイツ語', 'french': 'フランス語',
                    'chinese': '中国語', 'korean': '韓国語'}),
    ('理科', '◇', {'physics': '物理・物理基礎', 'chemistry': '化学・化学基礎',
                  'biology': '生物・生物基礎', 'earth-science': '地学・地学基礎', 'science-basics': '理科基礎の選択'}),
    ('地理歴史', '地', {'geography': '地理', 'japanese-history': '日本史', 'world-history': '世界史'}),
    ('公民', '公', {'civics': '公共・倫理・政治経済', 'geography-history-mix': '地理総合／歴史総合／公共'}),
    ('情報', '01', {'information': '情報Ⅰ'}),
)
SUBJECTS = {key: title for _, _, subjects in GROUPS for key, title in subjects.items()}
SKILLS = {
    'graphs': ('表やグラフを読む', '軸・単位・傾き・比較する区間を確かめる。', '▥'),
    'model': ('条件を式や図にする', '変わる量と決まっている量を書き出す。', 'ƒ'),
    'evidence': ('根拠を探す', '選択肢のどの言葉を、資料のどこで確かめるか。', '⌕'),
    'compare': ('条件をそろえて比べる', '何を同じにして、何を変えたかを見分ける。', '≍'),
    'timeline': ('時間順に整理する', '出来事や値を、変化が起きた順に並べる。', '⋯'),
    'structure': ('構造を見抜く', '文の骨格や、図・式の対応する部分をつかむ。', '▤'),
}
NOTES = {
    'math': [('高校数学ノート', '/works/math-notes/items/'), ('受験数学マップ', '/todai-math-map/')],
    'english': [('英文法ノート', '/works/eng-grammar-notes/items/'), ('埼玉大英語の学習チェック', '/works/saitama-english/')],
    'physics': [('高校物理ノート', '/works/physics-notes/items/')],
    'chemistry': [('高校化学ノート', '/works/chem-notes/items/')],
    'biology': [('埼玉大理科の学習チェック', '/works/saitama-science/')],
}
CURRICULUM = 'https://www.dnc.ac.jp/kyotsu/shiken_jouhou/r9/'
BOOKS = (
    ('チャート式 基礎からの数学（数研出版）', '典型題の目印と一手目を、例題のそばに置く。',
     'https://www.chart.co.jp/top/chart/kou.html'),
    ('理系数学の良問プラチカ（河合出版）', 'どの型か指定されていない問題で、方針を選ぶ練習をする。',
     'https://www.kawai-publishing.jp/book/?isbn=978-4-7772-2721-1'),
    ('やさしい理系数学（河合出版）', '融合問題では、方針が通用する条件まで考える。',
     'https://www.kawai-publishing.jp/book/?isbn=978-4-7772-1363-4'),
    ('セミナー化学（第一学習社）', '単元の確認から例題、基本演習、総合演習へ段階をつくる。',
     'https://www.daiichi-g.co.jp/pr/sb/42/books/47727_2702'),
)
LINKS = (('解法ガイド', BASE), ('復習・苦手', BASE + 'review/'),
         ('過去問', BASE + 'papers/'), ('配布・印刷', BASE + 'share/'))


def link(label, href, css=''):
    classes = f' class="{css}"' if css else ''
    return f'<a{classes} href="{escape(href, quote=True)}">{escape(label)}</a>'


def links(items, css=''):
    return ''.join(link(label, href, css) for label, href in items)


def lesson_href(item):
    return f'{BASE}{item["subject"]}/{item["id"]}/'


def load_lessons():
    lessons = []
    ids = set()
    for path in sorted((GUIDE / 'content').glob('*.json')):
        for item in json.loads(path.read_text()):
            ident = item['id']
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', ident) or ident in ids:
                raise ValueError(f'{path.name}: duplicate or invalid ID {ident}')
            ids.add(ident)
            if item['subject'] not in SUBJECTS or item['skill'] not in SKILLS:
                raise ValueError(f'{ident}: unknown subject or skill')
            item.setdefault('level', 'standard')
            if item['level'] not in LEVEL:
                raise ValueError(f'{ident}: unknown level')
            for field in ('unit', 'title', 'cue', 'problem', 'answer', 'pitfall'):
                if not isinstance(item[field], str) or not item[field].strip():
                    raise ValueError(f'{ident}: invalid {field}')
            if not isinstance(item['steps'], list) or len(item['steps']) < 2:
                raise ValueError(f'{ident}: at least two steps are required')
            for reference in item.get('links', []):
                href = reference['href']
                address = urlsplit(href)
                if address.scheme == 'https' and address.netloc:
                    continue
                disk_path = ROOT / address.path.lstrip('/')
                if not href.startswith('/') or href.startswith('//') or not (
                    disk_path.is_file() or (disk_path / 'index.html').is_file()
                ):
                    raise ValueError(f'{ident}: invalid lesson reference {href}')
            lessons.append(item)
    if set(SUBJECTS) != {c['subject'] for c in lessons}:
        raise ValueError('Some subjects do not have lessons')
    return lessons


def page(title, summary, path, body, *, scripts='', inline_css='', offline=False):
    metadata = '<meta name="robots" content="noindex">' if offline else f'''
<link rel="canonical" href="{SITE}{path}">
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(summary)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}{BASE}study-900.webp">
<link rel="icon" href="/favicon.png">
<link rel="stylesheet" href="{BASE}guide.css">'''
    nav = '' if offline else f'''<header class="top"><div class="wrap top-row">
<a class="brand" href="{BASE}">受験の解法ガイド</a><nav aria-label="学習メニュー">{links(LINKS[1:])}</nav>
</div></header>'''
    footer = '' if offline else f'''<footer class="site-footer wrap">
<nav aria-label="サイト案内">{links((('受験・学習', '/juken/'), ('小さな実験室', '/'),
 ('運営者情報', '/about/'), ('教材の誤りを知らせる', '/contact/')))}</nav></footer>'''
    style = f'<style>{inline_css}</style>' if inline_css else ''
    return f'''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{escape(summary)}">
<title>{escape(title)}</title>{metadata}
{style}
</head>
<body>
<a class="skip" href="#main">本文へ</a>
{nav}
<main class="wrap" id="main">{body}
</main>{footer}
{scripts}
</body></html>
'''


def figure_block(figure):
    if not figure:
        return ''
    caption = escape(figure['caption'])
    head = ''.join(f'<th scope="col">{escape(value)}</th>' for value in figure['columns'])
    rows = ''.join(
        '<tr>' + f'<th scope="row">{escape(row[0])}</th>'
        + ''.join(f'<td>{escape(value)}</td>' for value in row[1:]) + '</tr>'
        for row in figure['rows']
    )
    return f'<table class="worked-table"><caption>{caption}</caption><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>'


def related_lessons(item, catalog):
    affinities = {
        'conditional-prob': ('遺伝', '確率'),
        'tangent': ('傾き', '速度'),
        'info-data': ('相関', '対照', 'グラフ'),
        'info-simulation': ('条件', '対照', '実験'),
    }
    terms = affinities.get(item['id'], ())
    matches = (entry for entry in catalog
               if entry['skill'] == item['skill'] and entry['subject'] != item['subject'])
    matches = sorted(matches, key=lambda entry: -sum(
        term in entry['title'] + entry['unit'] + entry['cue'] for term in terms))
    related = []
    used = set()
    for entry in matches:
        if entry['subject'] in used:
            continue
        used.add(entry['subject'])
        related.append(entry)
        if len(related) == 2:
            break
    return related


def lesson(item, catalog, offline=False, heading="h2"):
    ident = item['id']
    title = escape(item['title'])
    skill_label = SKILLS[item['skill']][0]
    subject = SUBJECTS[item['subject']]
    level = LEVEL[item['level']]
    steps = ''.join(f'<li>{escape(step)}</li>' for step in item['steps'])
    related = []
    for entry in related_lessons(item, catalog):
        label = SUBJECTS[entry['subject']] + ' · ' + entry['title']
        related.append((label, '#' + entry['id'] if offline else lesson_href(entry)))
    refs = [] if offline else [(ref['label'], ref['href']) for ref in item.get('links', [])]
    skill_url = f'{BASE}?skill={item["skill"]}#find'
    skill_heading = escape(skill_label) if offline else link(skill_label, skill_url)
    extra = ''
    if related or refs:
        extra = f'''<details class="related"><summary>つながる知識・詳しい解説</summary>
<p class="muted">共通する考え方　{skill_heading}</p><div class="related-links">{links(related + refs)}</div></details>'''
    anchor = '#' + ident if offline else lesson_href(item)
    figure = item.get('figure', {})
    diagram = figure_block(figure)
    problem_figure = figure.get('placement') == 'problem'
    return f'''
<article class="lesson" id="{ident}" data-subject-label="{escape(subject)}" data-unit="{escape(item["unit"])}" data-review-anchor="{anchor}">
<header><p class="eyebrow">{escape(item["unit"])} <span class="level">{level}</span></p>
<{heading}>{title}</{heading}></header>
<div class="cue"><strong>見分け方</strong><p>{escape(item["cue"])}</p></div>
<div class="example" data-problem><strong>例題</strong><p>{escape(item["problem"])}</p>{diagram if problem_figure else ""}</div>
<details><summary>最初の一手を見る</summary><ol class="steps">{steps}</ol></details>
<details class="solution"><summary>解答とつまずきやすい所</summary>
<p data-answer>{escape(item["answer"])}</p>
{"" if problem_figure else diagram}
<p class="pitfall"><strong>確認</strong> {escape(item["pitfall"])}</p></details>
<div data-practice hidden></div>
{extra}
</article>'''


def art():
    return '''<picture class="hero-image">
<source media="(max-width: 680px)" srcset="study-480.webp 480w, study-900.webp 900w" sizes="92vw">
<img src="study-900.webp" width="900" height="600" alt="" decoding="async" fetchpriority="high">
</picture>'''


def subject_grid(totals):
    tiles = []
    for label, icon, subjects in GROUPS:
        entries = ((f'{name}　{totals[key]}題', BASE + key + '/') for key, name in subjects.items())
        tiles.append(f'<div class="subject-group"><h3><span aria-hidden="true">{icon}</span>{label}</h3>'
                     f'<div>{links(entries)}</div></div>')
    return ''.join(tiles)


def course_cards():
    lessons = (
        ('基本を覚え直す', '最初の一手を隠して、問題文のどこが手がかりかを言えるようにする。',
         '二次関数の頂点', 'math/quad-complete/'),
        ('問題から方針を選ぶ', '条件が変わったときに、同じ道具が使えるかを確かめる。',
         '閉区間の最大・最小', 'math/quad-range/'),
        ('複数の考え方をつなぐ', '図を描き、場合分けの境界と根拠まで書く。',
         '動く定義域の最小値', 'math/quad-moving/'),
        ('本番形式で試す', '時間を測って解き、止まった単元を記録して戻る。',
         '公式の過去問を探す', 'papers/'),
    )
    cards = ''.join(
        f'<li><h3>{title}</h3><p>{text}</p>{link(example, BASE + href, "text-link")}</li>'
        for title, text, example, href in lessons)
    paths = (
        ('理科　数字から反応へ', '単位をそろえ、余る物質まで判断する。', (
            ('モル濃度を求める', BASE + 'chemistry/chemistry-concentration-density/'),
            ('反応する量を決める', BASE + 'chemistry/chemistry-limiting-reactant/'),
            ('中和に当てはめる', BASE + 'chemistry/chemistry-neutralization-amounts/'),
        )),
        ('国語・英語　文から根拠を拾う', '一文の骨格から、選択肢の根拠へ進む。', (
            ('英文の主節を取る', BASE + 'english/english-main-clause/'),
            ('文章の主張を探す', BASE + 'japanese/japanese-modern-claim/'),
            ('根拠の範囲を判断する', BASE + 'english/english-inference-limits/'),
        )),
        ('地理・情報・生物　資料から言えること', '割合、因果、対照を区別して結論を出す。', (
            ('割合を人数に直す', BASE + 'geography/geography-population-pyramid/'),
            ('相関と因果を区別する', BASE + 'information/info-data/'),
            ('条件をそろえて比較する', BASE + 'biology/biology-control-light/'),
        )),
    )
    tracks = ''.join(f'<div class="subject-group"><h3>{title}</h3><p class="muted">{description}</p>'
                     f'<ol class="steps">{"".join(f"<li>{link(label, href)}</li>" for label, href in goals)}</ol></div>'
                     for title, description, goals in paths)
    return f'''<section id="route" class="section">
<header class="section-head"><div><p class="eyebrow">独学のミニ講座</p><h2>例題から過去問まで</h2></div>
<p>数学の二次関数で進み方を試せます。いま難しい段階から始めてください。</p></header>
<ol class="course">{cards}</ol>
<h3 class="browse-title">ほかのミニ講座</h3><div class="subject-grid">{tracks}</div>
<div class="quick-links">{link("共通テスト形式の演習", "/juken/kyotsu/")}</div>
</section>'''


def skill_tiles(totals):
    return ''.join(f'''<a class="skill-card" href="?skill={key}#find">
<span aria-hidden="true">{icon}</span><h3>{label}</h3><p>{description}</p><small>{totals[key]}題</small></a>'''
        for key, (label, description, icon) in SKILLS.items())


def home(catalog):
    subject_totals = Counter(c['subject'] for c in catalog)
    skill_totals = Counter(c['skill'] for c in catalog)
    choices = ''.join(f'<option value="{key}">{name}</option>' for key, name in SUBJECTS.items())
    skill_choices = ''.join(f'<option value="{key}">{value[0]}</option>' for key, value in SKILLS.items())
    level_choices = ''.join(f'<option value="{key}">{name}</option>' for key, name in LEVEL.items())
    book_items = ''.join(f'<li>{link(book, href)}<p>{description}</p></li>' for book, description, href in BOOKS)
    body = f'''
<section class="hero">
<div><p class="eyebrow">大学受験を、ひとりで進めるために</p>
<h1>受験の解法<br class="wide-break">ガイド</h1>
<p class="intro">問題の見分け方から、最初の一手、次の復習まで。</p>
<div class="actions"><a class="button primary" href="#find">解法を探す</a><a class="button" href="#route">学ぶ順番を見る</a></div>
<p class="muted">無料・広告なし・登録不要</p></div>
{art()}
</section>
<section id="find" class="section">
<header class="section-head"><div><p class="eyebrow">{len(catalog)}のオリジナル例題</p><h2>解法を探す</h2></div>
<p>科目名、単元名、問題の特徴で探せます。</p></header>
<form id="guide-search" class="search-panel" role="search" hidden>
<label class="query">キーワード<input name="q" type="search" placeholder="例　最大値、英文の主語、実験の対照" enterkeyhint="search"></label>
<div class="filters">
<label>科目<select name="subject"><option value="">すべての科目</option>{choices}</select></label>
<label>考え方<select name="skill"><option value="">すべての考え方</option>{skill_choices}</select></label>
<label>難度<select name="level"><option value="">すべての難度</option>{level_choices}</select></label>
</div>
<label class="scope"><input type="checkbox" name="notes"> 既存のノート・数学マップも探す</label>
<button type="submit" class="button primary">検索</button>
</form>
<div id="guide-results" class="results" hidden>
<p id="result-status" role="status"></p><ul id="result-list"></ul>
<button type="button" id="result-more" class="button" hidden>続きの結果を表示</button>
</div>
<h3 class="browse-title">科目から選ぶ</h3>
<div class="subject-grid">{subject_grid(subject_totals)}</div>
<p class="muted">共通テストの7教科に対応した入門教材です。収録問題数と単元は科目ごとに異なります。受験科目は志望校の募集要項で確認してください。</p>
</section>
{course_cards()}
<section class="section" id="connections">
<header class="section-head"><div><p class="eyebrow">科目をまたいで学ぶ</p><h2>解き方の共通点</h2></div>
<p>たとえばグラフの軸を読む力は、数学でも理科でも地理でも使えます。</p></header>
<div class="skill-grid">{skill_tiles(skill_totals)}</div>
</section>
<section class="section access-band" id="access">
<div><h2>紙でも、電波がない場所でも。</h2><p>問題を見てノートに解き、解説で答え合わせ。教材を保存するとオフラインで開けます。</p></div>
<div class="actions"><a class="button primary" href="download.html" download="受験の解法ガイド.html">オフライン教材を保存</a>
<a class="button" href="share/">学校・図書館向け配布用紙</a></div>
</section>
<section class="section editorial" id="references">
<details><summary>教材づくりで参考にしたもの</summary>
<p>市販教材の学習の進め方を参考に、問題を見分ける練習と復習をひと続きに設計しました。このガイドの例題と解説は独自に作成しています。</p>
<ul>{book_items}</ul>
<p>単元ごとの探しやすさや、疑問と例題を短いページにつなぐ設計は、
{link("受験の月", "https://examist.jp/")}と{link("化学のグルメ", "https://kimika.net/pro.html")}の構成も参考にしました。</p>
<p>{link("共通テストの出題教科・科目（大学入試センター）", CURRICULUM)}</p>
</details></section>'''
    return page('受験の解法ガイド｜無料で学ぶ大学受験', '大学受験の解法を科目・単元・考え方から探せる無料教材。オリジナル例題、ミニ講座、復習、配布用紙。', BASE, body,
                scripts=f'<script src="{BASE}search.js" defer></script>')


def subject_page(subject, catalog):
    title = SUBJECTS[subject]
    entries = [entry for entry in catalog if entry['subject'] == subject]
    mentor = NOTES.get(subject, [])
    if mentor:
        further = f'<div class="quick-links" aria-label="関連教材">{links(mentor)}</div>'
    else:
        further = ''
    cards = ''.join(
        f'<li class="subject-group topic" id="{entry["id"]}"><p class="eyebrow">{escape(entry["unit"])}'
        f' <span class="level">{LEVEL[entry["level"]]}</span></p>'
        f'<h2>{link(entry["title"], lesson_href(entry), "text-link")}</h2><p>{escape(entry["cue"])}</p></li>'
        for entry in entries)
    body = f"""<header class="subject-head">
<a class="text-link" href="{BASE}#find">科目一覧</a>
<h1>{title}</h1>
<p>{len(entries)}題。知りたい解き方を選んで、例題を一問試せます。</p>
{further}</header>
<ul class="subject-grid topic-list">{cards}</ul>
<p class="quick-links"><a class="button" href="{BASE}#find">ほかの問題を探す</a></p>"""
    return page(title + 'の解法｜受験の解法ガイド',
                f'{title}の問題の見分け方、解法の手順、自作例題と解説を収録。無料・登録不要。',
                BASE + subject + '/', body)


def lesson_page(item, catalog):
    subject = item['subject']
    subject_title = SUBJECTS[subject]
    entries = [entry for entry in catalog if entry['subject'] == subject]
    index = entries.index(item)
    previous = entries[index - 1] if index > 0 else None
    following = entries[index + 1] if index + 1 < len(entries) else None
    jumps = [(entry['title'], lesson_href(entry)) for entry in (previous, following) if entry]
    unit_links = ((subject_title + 'の例題一覧', BASE + subject + '/'), ('解法を探す', BASE + '#find'))
    next_links = f'<section class="more-topic"><h2>同じ科目の例題</h2><div class="quick-links">{links(jumps)}</div></section>' if jumps else ''
    body = f"""<div class="lesson-page">
<nav class="lesson-nav" aria-label="教材の階層">{links(unit_links)}</nav>
{lesson(item, catalog, heading="h1")}
{next_links}
</div>"""
    return page(item['title'] + '｜' + item['unit'] + '｜受験の解法ガイド', item['cue'], lesson_href(item), body,
                scripts=f'<link rel="stylesheet" href="{BASE}review/practice.css"><script src="{BASE}practice.js" defer></script>')


PAPER_SOURCES = (
    ('大学入試センター', '共通テストの過去の試験情報', 'https://www.dnc.ac.jp/kyotsu/index.html'),
    ('長崎大学', '一般選抜前期など、学部入試の掲載・閲覧案内', 'https://www.nagasaki-u.ac.jp/nyugaku/admission/profile/'),
    ('熊本大学', '一般選抜などの問題・解答例・出題の意図', 'https://www.kumamoto-u.ac.jp/nyuushi/gakubunyushi/kakomon'),
    ('鹿児島大学', '過去の入試問題・解答例', 'https://www.kagoshima-u.ac.jp/exam/kakomon.html'),
    ('埼玉大学', '過去問の閲覧案内と外部公開先', 'https://www.saitama-u.ac.jp/entrance/exam_info/browse/'),
    ('香川大学', '一般選抜の入試過去問題', 'https://www.kagawa-u.ac.jp/admission/entrance_exam/past_exam/general/'),
    ('島根大学', '入試過去問題・出題意図・解答例', 'https://www.shimane-u.ac.jp/nyushi/admission_data/past_questions/'),
    ('京都大学', '一般選抜の試験問題と出題意図', 'https://www.kyoto-u.ac.jp/ja/admissions/undergrad/past-eq'),
    ('東京大学', '一般選抜等の試験問題および解答等', 'https://www.u-tokyo.ac.jp/ja/admissions/undergraduate/e01_04.html'),
)


def papers_page():
    sources = ''.join(
        f'<li class="subject-group">{link(name, href, "text-link")}<p>{escape(detail)}</p></li>'
        for name, detail, href in PAPER_SOURCES)
    body = f"""<header class="subject-head"><a class="text-link" href="../">解法ガイド</a>
<h1>過去問を探す・集める</h1>
<p>大学や入試センターの公開ページで解き、つまずいた単元を解法ガイドで確かめます。</p></header>
<section class="section" id="sources"><h2>公式の過去問</h2>
<p class="muted">選抜区分・年度によって公開範囲や閲覧方法が異なります。</p>
<ul class="subject-grid paper-list">{sources}</ul></section>
<section class="section" id="collection">
<h2>自分の過去問リスト</h2><p>公開ページのURLと、自分が詰まった単元を保存できます。保存先はこのブラウザです。</p>
<form id="paper-form" class="search-panel paper-form" hidden>
<label class="paper-wide">大学・試験名<input maxlength="100" name="name" required placeholder="例　長崎大学 前期"></label>
<label class="paper-wide">公開ページのURL<input type="url" inputmode="url" maxlength="1200" name="url" required placeholder="https://"></label>
<label>年度<input maxlength="24" name="year" inputmode="numeric" placeholder="例　2026"></label>
<label>科目<input maxlength="60" name="subject" placeholder="例　数学"></label>
<label class="paper-wide">つまずいた単元<input maxlength="100" name="unit" placeholder="例　二次関数"></label>
<button class="button primary" type="submit">リストに保存</button></form>
<p id="paper-status" role="status"></p>
<label class="search-panel" hidden>保存済みから絞り込む<input id="paper-filter" type="search"></label>
<p id="paper-count"></p><ul class="subject-grid paper-list" id="saved-papers"></ul>
<noscript><p>過去問リストの保存にはJavaScriptが必要です。</p></noscript>
</section>
<section class="section">
<h2>解いた後にすること</h2>
<ol class="steps"><li>途中で止まった大問とその理由を、式・用語・時間配分などに分けて書く。</li>
<li>単元名で解法を探し、短い例題で最初の一手を練習する。</li>
<li>数日後に同じ過去問に戻って、白紙からやり直す。</li></ol>
<div class="quick-links">{link("解法を探す", BASE + "#find")}{link("復習・苦手を見る", BASE + "review/")}</div>
</section>"""
    return page('過去問を探す・集める｜受験の解法ガイド',
                '大学・入試センターの公式過去問を探し、つまずいた単元をブラウザに記録できる無料のページ。',
                BASE + 'papers/', body, scripts='<script src="papers.js" defer></script>')


def offline_page(catalog):
    toc = ''.join(f'<li><a href="#section-{key}">{name}</a></li>' for key, name in SUBJECTS.items())
    subjects = ''.join(
        f'<section class="section" id="section-{key}"><h2 class="offline-title">{name}</h2><div class="lessons">'
        + ''.join(lesson(item, catalog, offline=True) for item in catalog if item['subject'] == key)
        + '</div></section>' for key, name in SUBJECTS.items())
    body = f'''<header class="subject-head"><p class="eyebrow">オフライン教材</p>
<h1>受験の解法ガイド</h1><p>インターネット接続なしで、全{len(catalog)}題の例題と解説を読めます。</p>
<p>復習や採点メモは、このファイルを開くブラウザが保存に対応している場合に使用できます。</p>
</header><details class="toc" open><summary>科目を選ぶ</summary><ul>{toc}</ul></details>
<section class="section"><h2>復習・苦手</h2><div data-review-list></div></section>
{subjects}<p>配布元　{link(SITE + BASE, SITE + BASE)}</p>'''
    css = (GUIDE / 'guide.css').read_text() + (GUIDE / 'review/practice.css').read_text()
    practice = (GUIDE / 'practice.js').read_text()
    return page('受験の解法ガイド｜オフライン教材', '受験の解法ガイドのオフライン版。',
                BASE + 'download.html', body, scripts=f'<script>{practice}</script>', inline_css=css, offline=True)


def write_indices(catalog):
    rows = []
    for entry in catalog:
        rows.append({
            'title': entry['title'], 'cue': entry['cue'], 'subject': entry['subject'],
            'subjectLabel': SUBJECTS[entry['subject']], 'unit': entry['unit'],
            'skill': entry['skill'], 'skillLabel': SKILLS[entry['skill']][0],
            'level': entry['level'], 'levelLabel': LEVEL[entry['level']], 'href': lesson_href(entry),
            'terms': ' '.join(entry.get('keywords', [])),
        })
    (GUIDE / 'search-index.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + '\n')
    rows = []
    sources = (
        ('math', '高校数学ノート', ROOT / 'works/math-notes/items'),
        ('math', '受験数学マップ', ROOT / 'todai-math-map/n'),
        ('english', '英文法ノート', ROOT / 'works/eng-grammar-notes/items'),
        ('physics', '高校物理ノート', ROOT / 'works/physics-notes/items'),
        ('chemistry', '高校化学ノート', ROOT / 'works/chem-notes/items'),
    )
    for subject, source, directory in sources:
        for path in sorted(directory.glob('*.html')):
            if path.name in ('index.html', 'patterns.html'):
                continue
            text = path.read_text(encoding='utf-8')
            title = re.search(r'<title>(.*?)</title>', text)
            if title:
                from html import unescape
                head = unescape(title[1]).split(' | ')[0].split('｜')[0]
                rows.append({'title': head, 'subject': subject, 'subjectLabel': SUBJECTS[subject],
                             'unit': source, 'href': '/' + path.relative_to(ROOT).as_posix(), 'note': True})
    (GUIDE / 'notes-index.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')) + '\n')
    return len(rows)


def update_sitemap(catalog):
    path = ROOT / 'sitemap.xml'
    text = path.read_text()
    text = re.sub(r'\s*<url>\s*<loc>https://kaitoinoue0921\.github\.io/juken/guide/[^<]*</loc>.*?</url>',
                  '', text, flags=re.S)
    routes = [BASE, BASE + 'share/', BASE + 'papers/'] + [BASE + key + '/' for key in SUBJECTS]
    routes.extend(lesson_href(item) for item in catalog)
    entries = ''.join(f'  <url>\n    <loc>{xml_escape(SITE + route)}</loc>\n  </url>\n' for route in routes)
    path.write_text(text.replace('</urlset>', entries + '</urlset>'))


def main():
    catalog = load_lessons()
    count = write_indices(catalog)
    (GUIDE / 'index.html').write_text(home(catalog))
    for subject in SUBJECTS:
        directory = GUIDE / subject
        directory.mkdir(exist_ok=True)
        (directory / 'index.html').write_text(subject_page(subject, catalog))
    for item in catalog:
        folder = GUIDE / item['subject'] / item['id']
        folder.mkdir(exist_ok=True)
        (folder / 'index.html').write_text(lesson_page(item, catalog))
    (GUIDE / 'download.html').write_text(offline_page(catalog))
    (GUIDE / 'papers/index.html').write_text(papers_page())
    update_sitemap(catalog)
    print(f'{len(catalog)} lessons over {len(SUBJECTS)} subjects; {count} index entries from existing materials')


if __name__ == '__main__':
    main()
