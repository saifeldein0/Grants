#!/usr/bin/env python3
"""Collect recent opportunity posts from WordPress-based listing sites into data/discovered.json.

Runs daily in GitHub Actions. Standard library only. The board's Discover panel filters
this digest by the user's field, so the digest itself stays broad.
"""
import datetime as dt, html, json, pathlib, re, sys, time, urllib.parse, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "scanner" / "sources.json").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "discovered.json"
UA = "grant-board-scanner/1.0 (+https://github.com/saifeldein0/Grants)"
OPP = re.compile(r"scholarship|fellowship|grant|programme|program|school|internship|award|funded|course|residency|bootcamp|call for", re.I)
TAG = re.compile(r"<[^>]+>")


def text(s):
    return re.sub(r"\s+", " ", html.unescape(TAG.sub(" ", s or ""))).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def posts(source, query, n):
    q = urllib.parse.urlencode({"search": query, "per_page": n, "orderby": "date",
                                "_fields": "id,date,link,title,excerpt"})
    for p in fetch(f"{source['base']}/wp-json/wp/v2/posts?{q}"):
        title = text((p.get("title") or {}).get("rendered"))
        if not title or not OPP.search(title):
            continue
        yield {"title": title,
               "excerpt": text((p.get("excerpt") or {}).get("rendered"))[:400],
               "link": p.get("link"),
               "date": (p.get("date") or "")[:10],
               "source": source["name"]}


def main():
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"items": []}
    items = {i["link"]: i for i in old.get("items", []) if i.get("link")}
    report = {}
    for s in CFG["sources"]:
        got = 0
        try:
            for q in CFG["queries"]:
                for it in posts(s, q, CFG["per_query"]):
                    if it["link"] not in items:
                        got += 1
                    items[it["link"]] = it
                time.sleep(1)  # be polite
            report[s["name"]] = f"ok (+{got})"
        except Exception as e:  # one broken site must not stop the scan
            report[s["name"]] = f"failed: {e.__class__.__name__}"
    cutoff = (dt.date.today() - dt.timedelta(days=CFG["keep_days"])).isoformat()
    kept = sorted((i for i in items.values() if i.get("date", "") >= cutoff),
                  key=lambda i: i.get("date", ""), reverse=True)
    out = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "sources": report, "items": kept}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1), f"\n{len(kept)} items kept")
    if all(v.startswith("failed") for v in report.values()):
        sys.exit("every source failed")


if __name__ == "__main__":
    main()
