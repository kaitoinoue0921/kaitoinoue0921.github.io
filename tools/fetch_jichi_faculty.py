#!/usr/bin/env python3
"""自治医大 教員の経歴・論文を researchmap から集めて jichi-faculty/data/faculty.json を作る。

使い方（ネットにつながる手元の環境で）:
  python3 tools/fetch_jichi_faculty.py

入力: jichi-faculty/roster.csv（name,name_en,department,position,researchmap,orcid）
  researchmap 列は https://researchmap.jp/ のパーマリンク（URL の末尾の文字列）。
  本人が公開している情報だけを使う。researchmap で公開されていない項目は取らない。
出力: jichi-faculty/data/faculty.json
"""
import csv, json, subprocess, sys, time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROSTER = ROOT / "jichi-faculty" / "roster.csv"
OUT = ROOT / "jichi-faculty" / "data" / "faculty.json"
API = "https://api.researchmap.jp/{pl}/{kind}?limit=100"


def get(pl, kind, start=1):
    # python の証明書設定に依存しないよう curl を使う
    r = subprocess.run(["curl", "-sL", "-m", "30", "-H", "Accept: application/json", "-A", "jichi-faculty-fetch",
                        "-w", "\n%{http_code}", API.format(pl=pl, kind=kind) + f"&start={start}"], capture_output=True)
    body, _, code = r.stdout.decode("utf-8", "replace").rpartition("\n")
    if code == "404":
        return {}
    if code != "200":
        raise RuntimeError(f"HTTP {code}")
    return json.loads(body)


def items(data):
    out = list(data.get("items", []))
    for g in data.get("@graph", []):
        out += g.get("items", [])
    return out


def all_items(pl, kind):
    """researchmap は1回に返す件数に上限があるので、next リンクが無くなるまで続ける。"""
    out, start = [], 1
    while True:
        d = get(pl, kind, start)
        got = items(d)
        out += got
        total = d.get("total_items", len(out))
        if not got or len(out) >= total:
            return out
        start += len(got)


def ja_en(v):
    if isinstance(v, dict):
        return v.get("ja") or v.get("en") or ""
    return v or ""


def authors(v):
    if not isinstance(v, dict):
        return ""
    lst = v.get("ja") or v.get("en") or []
    names = [a.get("name", "") for a in lst if isinstance(a, dict)]
    # ファイルが大きくなりすぎるので先頭3人まで
    return ", ".join(names[:3]) + (" ほか" if len(names) > 3 else "")


def paper(it):
    ids = it.get("identifiers") or {}
    p = {
        "date": (it.get("publication_date") or "")[:10],
        "title": ja_en(it.get("paper_title")),
        "authors": authors(it.get("authors")),
        "journal": ja_en(it.get("publication_name")),
    }
    # 空の項目は省いてファイルを軽くする
    if (ids.get("doi") or [""])[0]:
        p["doi"] = ids["doi"][0]
    if (ids.get("pm_id") or [""])[0]:
        p["pmid"] = ids["pm_id"][0]
    if it.get("referee"):
        p["peer"] = 1
    return p


def career(it, kind):
    aff = ja_en(it.get("affiliation"))
    job = ja_en(it.get("job"))
    dept = ja_en(it.get("section")) if kind == "research_experience" else ja_en(it.get("department"))
    deg = " ".join([ja_en(it.get("course")), ja_en(it.get("degree"))]).strip() if kind == "education" else ""
    return {
        "kind": "学歴" if kind == "education" else "職歴",
        "from": (it.get("from_date") or "")[:7],
        "to": "現在" if (it.get("to_date") or "").startswith("9999") else (it.get("to_date") or "")[:7],
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
                    p["papers"] = sorted((paper(x) for x in all_items(pl, "published_papers")),
                                         key=lambda x: x["date"], reverse=True)
                    for kind in ("education", "research_experience"):
                        p["careers"] += [career(x, kind) for x in all_items(pl, kind)]
                    p["careers"].sort(key=lambda c: c["from"])
                except Exception as e:  # 1人の失敗で全体を止めない
                    print(f"[警告] {p['name']} ({pl}): {e}", file=sys.stderr)
                time.sleep(1)
            people.append(p)
            print(f"{p['name']}: 論文 {len(p['papers'])} 件, 経歴 {len(p['careers'])} 件")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"updated": date.today().isoformat(), "people": people},
                              ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("->", OUT)


if __name__ == "__main__":
    main()
