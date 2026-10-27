#!/usr/bin/env python3
"""自治医大「研究者情報」(kyouingyousekidb.jichi.ac.jp) の医学部の講座ページから名簿を集め、
jichi-faculty/roster.csv（name,name_en,department,position,researchmap,orcid）を作る。

大学の公開ページに載っている名前・所属・職名と、各人のページにある researchmap の
パーマリンクだけを使う。robots.txt の Crawl-delay に合わせて1秒空ける。
使い方: python3 tools/build_jichi_roster.py
"""
import csv, html, re, subprocess, sys, time, urllib.parse
from pathlib import Path

BASE = "https://kyouingyousekidb.jichi.ac.jp"
OUT = Path(__file__).resolve().parent.parent / "jichi-faculty" / "roster.csv"
UA = "jichi-faculty-roster (personal study project)"


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
    rows, seen = [], {}
    for page in dept_pages():
        people, total = collect(page)
        print(page, total, len(people))
        for p in people:
            if p["slug"] in seen:
                continue
            seen[p["slug"]] = p
            rows.append(p)
    print("人数", len(rows))
    for i, p in enumerate(rows, 1):
        p["researchmap"] = permalink(p["slug"])
        if i % 25 == 0:
            print(i, "/", len(rows), flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "name_en", "department", "position", "researchmap", "orcid"])
        for p in rows:
            w.writerow([p["name"], p["name_en"], p["department"], p["position"], p["researchmap"], ""])
    print("->", OUT)


if __name__ == "__main__":
    main()
