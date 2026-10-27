#!/usr/bin/env python3
"""jichi-faculty/data/faculty.json の論文に、Crossref の被引用数を足す。

DOI のある論文ごとに "c"（Crossref での被引用数）を入れ、教員ごとに
  cit: 被引用数の合計 / h: h指数 / cn: 被引用数が分かった論文の数
を入れる。researchmap の登録論文だけが対象で、Crossref に載らない引用は数えない
（Scopus や Google Scholar より少なく出る）。何度実行しても同じ形になる。
使い方: python3 tools/fetch_citations.py   （fetch_jichi_faculty.py のあとに実行）
"""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "jichi-faculty" / "data" / "faculty.json"
API = "https://api.crossref.org/works?rows=100&select=DOI,is-referenced-by-count&filter="
BATCH = 50


def fetch(dois):
    q = ",".join("doi:" + urllib.parse.quote(d, safe="/") for d in dois)
    req = urllib.request.Request(API + q, headers={"User-Agent": "jichi-faculty-fetch"})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                items = json.load(r)["message"]["items"]
            return {it["DOI"].lower(): it.get("is-referenced-by-count", 0) for it in items}
        except Exception as e:
            print("再試行", i + 1, e, file=sys.stderr)
            time.sleep(3 * (i + 1))
    return {}


def hindex(cs):
    cs = sorted(cs, reverse=True)
    return sum(1 for i, c in enumerate(cs, 1) if c >= i)


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    dois = sorted({p["doi"].lower() for x in d["people"] for p in x["papers"] if p.get("doi") and "," not in p["doi"]})
    cites = {}
    for i in range(0, len(dois), BATCH):
        cites.update(fetch(dois[i:i + BATCH]))
        if (i // BATCH) % 20 == 0:
            print(f"{min(i + BATCH, len(dois))} / {len(dois)}", flush=True)
        time.sleep(0.3)
    print("被引用数が分かった DOI:", len(cites), "/", len(dois))
    for x in d["people"]:
        cs = []
        for p in x["papers"]:
            c = cites.get((p.get("doi") or "").lower())
            if c is None:
                p.pop("c", None)
            else:
                p["c"] = c
                cs.append(c)
        x.pop("cit", None), x.pop("h", None), x.pop("cn", None)
        if cs:
            x["cit"], x["h"], x["cn"] = sum(cs), hindex(cs), len(cs)
    d["cited"] = time.strftime("%Y-%m-%d")
    DATA.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("->", DATA)


if __name__ == "__main__":
    main()
