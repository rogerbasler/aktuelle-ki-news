#!/usr/bin/env python3
"""Schritt 3: Linkprüfung. Jede finale Quelle wird zweimal geprüft (HTTP 200,
Ziel-URL ist ein Artikel und keine Übersichtsseite). Ausgefallene Meldungen
werden durch Reserven derselben Kategorie ersetzt. Das Ergebnis landet in
der Ausgabe unter "link_check".

Aufruf: python3 pipeline/verify_links.py [--date YYYY-MM-DD]
"""
import argparse
import json
import re
import sys
import time
from datetime import date

import requests

import config

HEADERS = {"User-Agent": config.USER_AGENT, "Accept-Language": "de,en;q=0.8"}
OVERVIEW = re.compile(r"/(tag|thema|category|topics?|news/?$|technik/ki/?$)", re.I)


def check_once(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True, stream=True)
        final = r.url.split("?")[0]
        r.close()
        ok = r.status_code == 200 and not OVERVIEW.search(final) and len(final) > 30
        return ok, r.status_code, final
    except Exception as e:  # noqa: BLE001
        return False, 0, str(e)[:120]


def check(url):
    runs = []
    for _ in range(2):
        runs.append(check_once(url))
        time.sleep(1.0)
    ok = all(r[0] for r in runs)
    return {"url": url, "ok": ok, "status": [r[1] for r in runs], "final_url": runs[-1][2]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    args = ap.parse_args()
    path = config.EDITIONS / f"{args.date}.json"
    edition = json.loads(path.read_text(encoding="utf-8"))
    reserves = edition.get("reserves", [])
    report, kept = [], []
    for it in edition["items"]:
        res = check(it["url"])
        report.append(res)
        if res["ok"]:
            it["url"] = res["final_url"] if res["final_url"].startswith("http") else it["url"]
            kept.append(it)
            continue
        print(f"ausgefallen: {it['url']} {res['status']}", file=sys.stderr)
        replacement = None
        for r in list(reserves):
            if r["category"] == it["category"]:
                rr = check(r["url"])
                report.append(rr)
                reserves.remove(r)
                if rr["ok"]:
                    replacement = r
                    break
        if replacement:
            print(f"ersetzt durch Reserve: {replacement['url']}", file=sys.stderr)
            kept.append(replacement)
        else:
            print("keine Reserve verfügbar, Meldung entfällt", file=sys.stderr)
    edition["items"] = kept
    edition["link_check"] = {"checked_at": date.today().isoformat(), "results": report,
                             "visible_items": len(kept)}
    edition.pop("reserves", None)
    path.write_text(json.dumps(edition, ensure_ascii=False, indent=2), encoding="utf-8")
    bad = [r for r in report if not r["ok"]]
    print(f"{len(report)} Prüfungen, {len(bad)} fehlgeschlagen, {len(kept)} Meldungen sichtbar")
    if len(kept) != 15:
        print("WARNUNG: nicht genau 15 Meldungen", file=sys.stderr)


if __name__ == "__main__":
    main()
