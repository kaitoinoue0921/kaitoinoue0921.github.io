#!/usr/bin/env python3
"""各教員の被引用数の上位N本（DOI あり）について、PubMed から要旨を取る。

要旨そのものは公開しない（著作物のため）。要約を書くための作業用ファイルに出す。
使い方: python3 tools/fetch_abstracts.py OUT.json [N=3]
出力: {doi: {"pmid","title","abstract"}}（要旨が取れた論文だけ）
"""
import json, re, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "jichi-faculty" / "data" / "faculty.json"
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
UA = {"User-Agent": "jichi-faculty-fetch"}


def get(url):
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            print("再試行", i + 1, e, file=sys.stderr)
            time.sleep(2 * (i + 1))
    return ""


def pmid_of(doi):
    q = urllib.parse.quote(f'"{doi}"[AID]')
    x = get(f"{EU}esearch.fcgi?db=pubmed&retmode=json&term={q}")
    time.sleep(0.4)
    try:
        ids = json.loads(x)["esearchresult"]["idlist"]
    except Exception:
        return ""
    return ids[0] if len(ids) == 1 else ""


def main():
    out, n = Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 3
    d = json.loads(DATA.read_text(encoding="utf-8"))
    dois = {}
    for x in d["people"]:
        top = sorted((p for p in x["papers"] if p.get("c") and p.get("doi")), key=lambda p: -p["c"])[:n]
        for p in top:
            dois[p["doi"].lower()] = p.get("pmid") or ""
    print("対象の論文:", len(dois), flush=True)
    for i, doi in enumerate(dois, 1):
        if not dois[doi]:
            dois[doi] = pmid_of(doi)
        if i % 100 == 0:
            print(i, "/", len(dois), flush=True)
    pm = {v: k for k, v in dois.items() if v}
    res = {}
    ids = list(pm)
    for i in range(0, len(ids), 100):
        xml = get(f"{EU}efetch.fcgi?db=pubmed&retmode=xml&id={','.join(ids[i:i+100])}")
        time.sleep(0.4)
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        for art in root.iter("PubmedArticle"):
            pid = art.findtext(".//PMID")
            ab = " ".join("".join(t.itertext()).strip() for t in art.iter("AbstractText"))
            title = "".join(art.find(".//ArticleTitle").itertext()) if art.find(".//ArticleTitle") is not None else ""
            if pid in pm and ab:
                res[pm[pid]] = {"pmid": pid, "title": title, "abstract": re.sub(r"\s+", " ", ab)}
    out.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
    print("要旨が取れた:", len(res), "/", len(dois), "->", out)


if __name__ == "__main__":
    main()
