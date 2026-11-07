#!/usr/bin/env python3
"""Build a single-file grant board: splice a JSON dataset into src/template.html.

Usage:
  python build.py                                  # sample data -> index.html
  python build.py --data my-data.json --out my-board.html --title "Sara's grant board"
"""
import argparse, datetime, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
DEFAULT_DIGEST = "https://raw.githubusercontent.com/saifeldein0/Grants/main/data/discovered.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=ROOT / "data" / "sample-data.json")
    ap.add_argument("--out", default=ROOT / "index.html")
    ap.add_argument("--title", default=None, help="heading shown on the board")
    ap.add_argument("--version", default=datetime.date.today().isoformat(), help="data version label")
    ap.add_argument("--digest", default=DEFAULT_DIGEST, help="URL of discovered.json ('' to disable)")
    a = ap.parse_args()

    raw = json.loads(pathlib.Path(a.data).read_text(encoding="utf-8"))
    entries = raw["entries"] if isinstance(raw, dict) else raw
    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate ids in data file")

    html = (ROOT / "src" / "template.html").read_text(encoding="utf-8")
    payload = json.dumps(entries, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (html.replace("__DATA__", payload)
                .replace("__DATA_VERSION__", a.version)
                .replace("__DIGEST_URL__", a.digest))
    if a.title:
        html = html.replace("<h1>Grant board</h1>", f"<h1>{a.title}</h1>", 1)
    pathlib.Path(a.out).write_text(html, encoding="utf-8")
    print(f"wrote {a.out} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
