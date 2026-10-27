#!/usr/bin/env python3
"""自治医大「研究者情報」(kyouingyousekidb.jichi.ac.jp) の医学部の講座ページから名簿を集め、
jichi-faculty/roster.csv（name,name_en,department,position,researchmap,orcid）を作る。

大学の公開ページに載っている名前・所属・職名と、各人のページにある researchmap の
パーマリンクだけを使う。robots.txt の Crawl-delay に合わせて1秒空ける。
使い方: python3 tools/build_jichi_roster.py          （名簿を作り直す）
        python3 tools/build_jichi_roster.py --add    （EXTRA_ROOTS の人だけ、今の名簿に足す）
"""
import csv, html, re, subprocess, sys, time, urllib.parse
from pathlib import Path

BASE = "https://kyouingyousekidb.jichi.ac.jp"
OUT = Path(__file__).resolve().parent.parent / "jichi-faculty" / "roster.csv"
UA = "jichi-faculty-roster (personal study project)"
# 医学部の下にない組織。そのページと、その下の部門ページを読む。
EXTRA_ROOTS = ["/地域医療学センター"]


def get(path):
    # python の証明書設定に依存しないよう curl を使う
    url = path if path.startswith("http") else BASE + urllib.parse.quote(path, safe="/?&=:#%")
    for i in range(3):
        r = subprocess.run(["curl", "-sL", "-m", "40", "-A", UA, url], capture_output=True)
        time.sleep(1)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
        print("再試行", url, file=sys.stderr)
        time.sleep(3)
    return ""


def text(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def cards(h):
    out = []
    for m in re.finditer(r'<div class="cvclients-card">(.*?)</li>', h, re.S):
        c = m.group(1)
        a = re.search(r'<div class="cvclients-name"><a href="([^"]+)"[^>]*>(.*?)</a>', c, re.S)
        if not a:
            continue
        slug = html.unescape(a.group(1)).split("?")[0].rsplit("/", 1)[-1]
        en = re.search(r'cvclients-name-en">(.*?)</div>', c, re.S)
        sec = re.search(r'cvclients-section">(.*?)</div>', c, re.S)
        job = re.search(r'cvclients-job">(.*?)</div>', c, re.S)
        out.append({"slug": slug, "name": text(a.group(2)), "name_en": text(en.group(1)) if en else "",
                    "department": text(sec.group(1)) if sec else "", "position": text(job.group(1)) if job else ""})
    return out


def dept_pages():
    h = get("/医学部")
    seen, res = set(), []
    for u in re.findall(r'<a[^>]*href="(/医学部/[^"]+)"', h):
        u = html.unescape(u)
        if u not in seen:
            seen.add(u)
            res.append(urllib.parse.unquote(u))
    return res


def with_children(root):
    h = get(root)
    kids, seen = [], set()
    for u in re.findall(r'<a[^>]*href="(' + re.escape(urllib.parse.quote(root, safe="/")) + r'/[^"]+)"', h):
        u = urllib.parse.unquote(html.unescape(u))
        if u not in seen:
            seen.add(u)
            kids.append(u)
    return [root] + kids


def collect(page):
    h = get(page)
    people = cards(h)
    tot = re.search(r"総件数 <span class=\"badge\">(\d+)", re.sub(r"\s+", " ", h))
    total = int(tot.group(1)) if tot else len(people)
    pg = re.search(r'(/cvclients/lists\?frame_id=\d+&amp;page_id=\d+&amp;limit=\d+)&amp;start=\d+', h)
    if total > len(people) and pg:
        base = html.unescape(pg.group(1))
        start = len(people) + 1
        while start <= total:
            more = cards(get(f"{base}&start={start}"))
            if not more:
                break
            people += more
            start += len(more)
    return people, total


def permalink(slug):
    h = get(f"/cvclients/researchers/{urllib.parse.quote(slug)}")
    m = re.search(r"researchmap\.jp/([A-Za-z0-9_.\-]+)/(?:published_papers|awards|research_experience|education)", h) \
        or re.search(r"researchmap\.jp/([A-Za-z0-9_.\-]+)[\"'/]", h)
    return m.group(1) if m and m.group(1) not in ("researchers", "search") else ""


def main():
    add = "--add" in sys.argv
    rows, seen = [], {}
    old = []
    if add:
        with open(OUT, encoding="utf-8") as f:
            old = list(csv.DictReader(f))
    pages = [q for r in EXTRA_ROOTS for q in with_children(r)]
    if not add:
        pages = dept_pages() + pages
    for page in pages:
        people, total = collect(page)
        print(page, total, len(people))
        for p in people:
            if p["slug"] in seen:
                continue
            seen[p["slug"]] = p
            rows.append(p)
    if add:  # 今の名簿にいる人（名前と英語名が同じ）は足さない
        have = {(r["name"], r["name_en"]) for r in old}
        rows = [p for p in rows if (p["name"], p["name_en"]) not in have]
    print("人数", len(rows))
    for i, p in enumerate(rows, 1):
        p["researchmap"] = permalink(p["slug"])
        if i % 25 == 0:
            print(i, "/", len(rows), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "a" if add else "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if not add:
            w.writerow(["name", "name_en", "department", "position", "researchmap", "orcid"])
        for p in rows:
            w.writerow([p["name"], p["name_en"], p["department"], p["position"], p["researchmap"], ""])
    print("->", OUT)


if __name__ == "__main__":
    main()
