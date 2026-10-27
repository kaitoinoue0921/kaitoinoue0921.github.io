#!/usr/bin/env python3
"""jichi-faculty/data/faculty.json に、researchmap の研究プロジェクト数（gr）と受賞数（aw）を足す。

researchmap で公開されている「研究課題（競争的資金など）」と「受賞」の件数だけを数える
（limit=1 で total_items を読む）。登録のない人・researchmap のない人は gr/aw を入れない。
使い方: python3 tools/fetch_grants.py   （fetch_jichi_faculty.py のあとに実行）
"""
import json, sys, time, urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "jichi-faculty" / "data" / "faculty.json"
API = "https://api.researchmap.jp/{pl}/{kind}?limit=1"


def total(pl, kind):
    req = urllib.request.Request(API.format(pl=pl, kind=kind),
                                 headers={"Accept": "application/json", "User-Agent": "jichi-faculty-fetch"})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return int(json.load(r).get("total_items", 0))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return 0
        except Exception as e:
            print("再試行", pl, kind, e, file=sys.stderr)
        time.sleep(2 * (i + 1))
    return None


def main():
    d = json.loads(DATA.read_text(encoding="utf-8"))
    for n, x in enumerate(d["people"], 1):
        x.pop("gr", None), x.pop("aw", None)
        pl = x.get("researchmap")
        if not pl:
            continue
        g, a = total(pl, "research_projects"), total(pl, "awards")
        if g is not None:
            x["gr"] = g
        if a is not None:
            x["aw"] = a
        time.sleep(0.5)
        if n % 50 == 0:
            print(n, "/", len(d["people"]), flush=True)
    d["granted"] = time.strftime("%Y-%m-%d")
    DATA.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("->", DATA)


if __name__ == "__main__":
    main()
