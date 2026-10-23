#!/usr/bin/env python3
"""トップページの検索窓用の索引 assets/search-index.json を作る。

材料:
  works/*-notes/items/*.html  ノートの項目ページ（index.html と patterns.html は除く）
  todai-math-map/n/*.html     受験数学マップのノードページ（index.html は除く）
どちらも <title> を拾い、最後の「｜」で「タイトル」と「補足（科目名など）」に分ける。
出力は [{"t":タイトル,"s":補足,"u":URL}, ...]。

ノートや数学マップを作り直したら（build_note_pages.py / build_mathmap_pages.py のあとで）、
これも実行する:  python3 tools/build_search_index.py
"""
import glob
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def entries(pattern, skip):
    for path in sorted(glob.glob(os.path.join(ROOT, pattern))):
        name = os.path.basename(path)
        if name in skip:
            continue
        with open(path, encoding="utf-8") as f:
            m = TITLE.search(f.read(8000))
        if not m:
            print("title なし:", path)
            continue
        text = html.unescape(m.group(1)).strip()
        t, _, s = text.rpartition("｜")
        if not t:
            t, s = text, ""
        url = "/" + os.path.relpath(path, ROOT).replace(os.sep, "/")
        yield {"t": t.strip(), "s": s.strip(), "u": url}


DESC = re.compile(r'<meta name="description" content="([^"]*)"')


def pages(paths):
    """ロードマップなど個別のページ。補足に meta description を入れて、本文の言葉（地域枠など）でも当たるようにする。"""
    for rel in paths:
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        head = open(path, encoding="utf-8").read(12000)
        m, d = TITLE.search(head), DESC.search(head)
        if not m:
            continue
        url = "/" + rel.replace(os.sep, "/")
        if url.endswith("/index.html"):
            url = url[:-len("index.html")]
        yield {"t": html.unescape(m.group(1)).strip(), "s": html.unescape(d.group(1)).strip() if d else "", "u": url}


def main():
    out = list(entries("works/*-notes/items/*.html", {"index.html", "patterns.html"}))
    n_notes = len(out)
    out += list(entries("todai-math-map/n/*.html", {"index.html"}))
    out += list(pages(["igakubu-roadmap/index.html", "igakubu-roadmap/plan.html", "igakubu-roadmap/units.html",
                       "igakubu-roadmap/region.html", "igakubu-roadmap/kyutei.html",
                       "igakubu-roadmap/chiikiwaku/site/index.html"] +
                      sorted(os.path.relpath(x, ROOT) for x in glob.glob(os.path.join(ROOT, "igakubu-roadmap/chiikiwaku/site/pref/*.html")))))
    dest = os.path.join(ROOT, "assets", "search-index.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print("ノート %d + 数学マップ %d = %d 件, %d bytes" % (n_notes, len(out) - n_notes, len(out), os.path.getsize(dest)))


if __name__ == "__main__":
    main()
