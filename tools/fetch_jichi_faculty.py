#!/usr/bin/env python3
"""自治医大 教員の経歴・論文を researchmap から集めて jichi-faculty/data/faculty.json を作る。

使い方（ネットにつながる手元の環境で）:
  python3 tools/fetch_jichi_faculty.py

入力: jichi-faculty/roster.csv（name,name_en,department,position,researchmap,orcid）
  researchmap 列は https://researchmap.jp/ のパーマリンク（URL の末尾の文字列）。
  本人が公開している情報だけを使う。researchmap で公開されていない項目は取らない。
出力: jichi-faculty/data/faculty.json
"""
import csv, json, sys, time, urllib.request, urllib.error
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROSTER = ROOT / "jichi-faculty" / "roster.csv"
OUT = ROOT / "jichi-faculty" / "data" / "faculty.json"
API = "https://api.researchmap.jp/{pl}/{kind}?limit={limit}&start={start}"
PAGE = 100


def get(pl, kind, start=1):
    req = urllib.request.Request(API.format(pl=pl, kind=kind, limit=PAGE, start=start),
                                 headers={"Accept": "application/json", "User-Agent": "jichi-faculty-fetch"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {}
        raise


def items(data):
    out = []
    for g in data.get("@graph", []):
        out += g.get("items", [])
    return out


def get_all(pl, kind):
    """PAGE 件ずつ start を進めて全件集める。"""
    out, start = [], 1
    while True:
        got = items(get(pl, kind, start))
        out += got
        if len(got) < PAGE:
            return out
        start += PAGE
        time.sleep(0.5)


def ja_en(v):
    if isinstance(v, dict):
        return v.get("ja") or v.get("en") or ""
    return v or ""


def authors(v):
    if not isinstance(v, dict):
        return ""
    lst = v.get("ja") or v.get("en") or []
    return ", ".join(a.get("name", "") for a in lst if isinstance(a, dict))


def paper(it):
    ids = it.get("identifiers") or {}
    return {
        "date": (it.get("publication_date") or "")[:10],
        "title": ja_en(it.get("paper_title")),
        "authors": authors(it.get("authors")),
        "journal": ja_en(it.get("publication_name")),
        "doi": (ids.get("doi") or [""])[0],
        "pmid": (ids.get("pm_id") or [""])[0],
        "type": it.get("published_paper_type", ""),
        "peer": it.get("referee"),
    }


def career(it, kind):
    aff = ja_en(it.get("affiliation"))
    job = ja_en(it.get("job"))
    dept = ja_en(it.get("section")) if kind == "research_experience" else ja_en(it.get("department"))
    deg = ja_en(it.get("degree")) if kind == "education" else ""
    return {
        "kind": "学歴" if kind == "education" else "職歴",
        "from": (it.get("from_date") or "")[:7],
        "to": (it.get("to_date") or "")[:7],
        "text": " ".join(x for x in [aff, dept, job, deg] if x),
    }


def main():
    if not ROSTER.exists():
        sys.exit("roster.csv がありません")
    people = []
    with open(ROSTER, encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), 1):
            pl = (row.get("researchmap") or "").strip()
            p = {k: (row.get(k) or "").strip() for k in ("name", "name_en", "department", "position", "orcid")}
            p["id"] = f"p{i:04d}"
            p["researchmap"] = pl
            p["papers"], p["careers"] = [], []
            if pl:
                try:
                    p["papers"] = sorted((paper(x) for x in get_all(pl, "published_papers")),
                                         key=lambda x: x["date"], reverse=True)
                    for kind in ("education", "research_experience"):
                        p["careers"] += [career(x, kind) for x in get_all(pl, kind)]
                    p["careers"].sort(key=lambda c: c["from"])
                except Exception as e:  # 1人の失敗で全体を止めない
                    print(f"[警告] {p['name']} ({pl}): {e}", file=sys.stderr)
                time.sleep(1)
            people.append(p)
            print(f"{p['name']}: 論文 {len(p['papers'])} 件, 経歴 {len(p['careers'])} 件")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated": date.today().isoformat(), "people": people},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("->", OUT)


if __name__ == "__main__":
    main()
