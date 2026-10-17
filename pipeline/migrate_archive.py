#!/usr/bin/env python3
"""Einmalige Migration: liest alle historischen index.html-Versionen aus der
Git-Historie und legt pro Ausgabe eine JSON-Datei unter data/editions/ an.

Aufruf:  python3 pipeline/migrate_archive.py
"""
import json
import re
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "editions"

MONTHS = {
    "januar": 1, "january": 1, "februar": 2, "february": 2, "märz": 3, "maerz": 3,
    "march": 3, "april": 4, "mai": 5, "may": 5, "juni": 6, "june": 6, "juli": 7,
    "july": 7, "august": 8, "september": 9, "oktober": 10, "october": 10,
    "november": 11, "dezember": 12, "december": 12,
}

CATEGORY_MAP = [
    (r"news der woche|ki news|k\.i\. news|news$", "news"),
    (r"tools|startups|start-ups", "tools"),
    (r"regulierung|ethik|regulation", "regulierung"),
    (r"stimmen|perspektiven|voices", "stimmen"),
    (r"business|society|gesellschaft|wirtschaft", "business"),
]


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def parse_date(text):
    """Erkennt 'DD. Monat YYYY', 'DD.MM.YYYY', 'YYYY-MM-DD'."""
    text = text or ""
    m = re.search(r"(\d{1,2})\.\s*([A-Za-zäöü]+)\s*(\d{4})", text)
    if m and m.group(2).lower() in MONTHS:
        return date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def category_key(title):
    t = title.lower()
    for pattern, key in CATEGORY_MAP:
        if re.search(pattern, t):
            return key
    return "news"


def source_name(url):
    u = url.lower()
    for key, name in [("t3n.de", "t3n"), ("heise.de", "heise"), ("handelsblatt", "Handelsblatt"),
                      ("techcrunch", "TechCrunch"), ("the-decoder", "The Decoder"),
                      ("aibreakfast", "AI Breakfast")]:
        if key in u:
            return name
    m = re.match(r"https?://(?:www\.)?([^/]+)", url)
    return m.group(1) if m else "Quelle"


def parse_html(html, commit, commit_date):
    soup = BeautifulSoup(html, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    header_text = " ".join(t.get_text(" ", strip=True) for t in soup.select("header, .subtitle, .date"))
    ed_date = parse_date(title) or parse_date(header_text) or commit_date
    items = []
    for section in soup.select("section"):
        h2 = section.find("h2")
        if not h2:
            continue
        if "podcast" in h2.get_text(" ", strip=True).lower():
            continue
        cat = category_key(h2.get_text(" ", strip=True))
        for h3 in section.find_all("h3"):
            container = h3.find_parent(class_=["news-item", "tool-card", "news-card"])
            if container is not None:
                nodes = container.find_all(["p", "a"])
            else:
                # Freies Layout: alle Geschwister bis zum nächsten h3 einsammeln
                nodes = []
                for sib in h3.next_siblings:
                    if getattr(sib, "name", None) == "h3":
                        break
                    if getattr(sib, "name", None) in ("p", "div", "ul"):
                        nodes.append(sib)
            link, generic = None, None
            for node in nodes:
                for a in ([node] if node.name == "a" else node.find_all("a", href=True)):
                    href = a.get("href", "")
                    if not href.startswith("http") or "ki-power.me" in href:
                        continue
                    if re.search(r"https?://(www\.)?[^/]+/?$", href) or "/thema/" in href or "/category/" in href or "/technik/ki/$" in href:
                        generic = generic or href
                    else:
                        link = link or href
            paras = [n.get_text(" ", strip=True) for n in nodes if n.name in ("p", "div", "ul")]
            summary = " ".join(p for p in paras
                               if not re.match(r"^\d{1,2}\.\s*\w+\s*\d{4}\s*\|", p)
                               and not p.lower().startswith("original-artikel")
                               and len(p) > 40)
            summary = re.sub(r"\[Quelle:[^\]]*\]", "", summary)
            summary = re.sub(r"\[\d+\]", "", summary)
            summary = re.sub(r"^Quelle:.*?\|\s*Datum:.*?\d{4}\s*", "", summary)
            summary = re.sub(r"\s+", " ", summary).strip()
            url = link or generic
            if not url or not summary:
                continue
            items.append({
                "category": cat,
                "url": url,
                "url_is_article": bool(link),
                "source": source_name(url),
                "de": {"title": h3.get_text(" ", strip=True), "summary": summary},
            })
    # Duplikate innerhalb einer Ausgabe (gleicher Titel) entfernen
    uniq, seen_titles = [], set()
    for it in items:
        key = it["de"]["title"].lower()
        if key in seen_titles:
            continue
        seen_titles.add(key)
        uniq.append(it)
    return ed_date, uniq


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    log = git("log", "--format=%h %cI", "--", "index.html").strip().splitlines()
    seen = {}
    for line in log:
        commit, iso = line.split(" ", 1)
        commit_date = datetime.fromisoformat(iso).date()
        html = git("show", f"{commit}:index.html")
        ed_date, items = parse_html(html, commit, commit_date)
        if len(items) < 3:
            print(f"skip {commit} ({ed_date}): nur {len(items)} Meldungen", file=sys.stderr)
            continue
        key = ed_date.isoformat()
        # Pro Datum nur die jüngste Version (das Log ist neueste zuerst)
        if key in seen:
            continue
        seen[key] = True
        edition = {
            "date": key,
            "week": ed_date.isocalendar()[1],
            "languages": ["de"],
            "migrated_from_commit": commit,
            "items": items,
            "podcast": {},
        }
        (OUT / f"{key}.json").write_text(json.dumps(edition, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{key}: {len(items)} Meldungen ({commit})")
    print(f"{len(seen)} Ausgaben migriert")


if __name__ == "__main__":
    main()
