#!/usr/bin/env python3
"""Schritt 1: Sammelt 40 bis 60 Kandidaten der letzten 7 Tage aus t3n, heise,
Handelsblatt und TechCrunch (RSS zuerst, HTML als Fallback) und speichert
die Recherche als JSON und Markdown unter data/research/.

Aufruf: python3 pipeline/fetch_sources.py [--date YYYY-MM-DD] [--days 7]
"""
import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from html import unescape

import feedparser
import requests
from bs4 import BeautifulSoup

import config

HEADERS = {"User-Agent": config.USER_AGENT, "Accept-Language": "de,en;q=0.8"}


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def clean(text):
    text = unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()


def is_ai(text):
    t = f" {text.lower()} "
    return any(f" {k} " in t or f" {k}-" in t or f"-{k} " in t or k in t for k in config.AI_KEYWORDS
               if len(k) > 2) or re.search(r"\bk\.?i\.?\b|\bai\b", t) is not None


def parse_feed(url, since):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        log(f"  feed fehlgeschlagen {url}: {e}")
        return []
    parsed = feedparser.parse(resp.content)
    out = []
    for e in parsed.entries:
        ts = e.get("published_parsed") or e.get("updated_parsed")
        if not ts:
            continue
        pub = datetime(*ts[:6], tzinfo=timezone.utc)
        if pub < since:
            continue
        out.append({
            "title": clean(e.get("title")),
            "url": e.get("link", "").split("?")[0],
            "summary": clean(e.get("summary") or e.get("description") or "")[:600],
            "published": pub.isoformat(),
        })
    return out


def parse_html(url, pattern, since):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        resp.raise_for_status()
    except Exception as e:  # noqa: BLE001
        log(f"  html fehlgeschlagen {url}: {e}")
        return []
    soup = BeautifulSoup(resp.text, "lxml")
    seen, out = set(), []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/"):
            href = re.match(r"https?://[^/]+", url).group(0) + href
        href = href.split("?")[0]
        if href in seen or not re.match(pattern, href):
            continue
        seen.add(href)
        title = clean(a.get_text(" ")) or clean(a.get("title", ""))
        if len(title) < 15:
            continue
        pub = None
        m = re.search(r"/(\d{4})/(\d{2})/(\d{2})/", href)
        if m:
            pub = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), tzinfo=timezone.utc)
            if pub < since:
                continue
        out.append({"title": title, "url": href, "summary": "",
                    "published": pub.isoformat() if pub else None})
    return out


def enrich(item):
    """Holt Veröffentlichungsdatum und Beschreibung aus den Meta-Tags des Artikels."""
    try:
        resp = requests.get(item["url"], headers=HEADERS, timeout=20)
        if resp.status_code != 200:
            return item
        soup = BeautifulSoup(resp.text, "lxml")
        meta = {m.get("property") or m.get("name"): m.get("content") for m in soup.find_all("meta")}
        if not item.get("published"):
            for k in ("article:published_time", "date", "pubdate", "datePublished", "og:updated_time"):
                if meta.get(k):
                    item["published"] = meta[k]
                    break
        if not item.get("summary"):
            item["summary"] = clean(meta.get("og:description") or meta.get("description") or "")[:600]
        item["final_url"] = resp.url.split("?")[0]
    except Exception as e:  # noqa: BLE001
        log(f"  enrich fehlgeschlagen {item['url']}: {e}")
    return item


def collect(run_date, days):
    since = datetime.combine(run_date, datetime.min.time(), tzinfo=timezone.utc) - timedelta(days=days)
    candidates = []
    for src in config.SOURCES:
        log(f"Quelle {src['name']}")
        items = []
        for feed in src["feeds"]:
            items = parse_feed(feed, since)
            if len(items) >= 5:
                log(f"  {len(items)} Einträge aus Feed {feed}")
                break
        if len(items) < 5:
            html_items = parse_html(src["html"], src["article_pattern"], since)
            log(f"  {len(html_items)} Einträge aus HTML-Fallback")
            known = {i["url"] for i in items}
            items += [i for i in html_items if i["url"] not in known]
        if src["ai_filter"]:
            items = [i for i in items if is_ai(i["title"] + " " + i["summary"])]
        for i in items:
            i["source"] = src["name"]
        # Ohne Datum: Artikel anfassen, um Datum und Beschreibung zu holen (max. 20 pro Quelle)
        todo = [i for i in items if not i.get("published") or not i.get("summary")][:20]
        for i in todo:
            enrich(i)
            time.sleep(0.3)
        items = [i for i in items if i.get("published") and datetime.fromisoformat(
            i["published"].replace("Z", "+00:00")).astimezone(timezone.utc) >= since]
        items.sort(key=lambda x: x["published"], reverse=True)
        candidates += items[:18]
        log(f"  -> {min(len(items), 18)} Kandidaten")
    # Duplikate über Quellen hinweg (gleiche URL)
    seen, uniq = set(), []
    for c in candidates:
        if c["url"] in seen:
            continue
        seen.add(c["url"])
        uniq.append(c)
    return uniq


def write_research(run_date, candidates):
    config.RESEARCH.mkdir(parents=True, exist_ok=True)
    (config.RESEARCH / f"{run_date}.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# Recherche KI Power Update, Stand {run_date}", "",
             f"{len(candidates)} Kandidaten aus den letzten 7 Tagen.", ""]
    for src in config.SOURCES:
        lines.append(f"## {src['name']}")
        for c in [c for c in candidates if c["source"] == src["name"]]:
            lines.append(f"- {c['published'][:10]} [{c['title']}]({c['url']})")
            if c.get("summary"):
                lines.append(f"  {c['summary'][:220]}")
        lines.append("")
    (config.RESEARCH / f"{run_date}.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--days", type=int, default=7)
    args = ap.parse_args()
    run_date = date.fromisoformat(args.date)
    candidates = collect(run_date, args.days)
    write_research(run_date, candidates)
    log(f"{len(candidates)} Kandidaten gespeichert unter data/research/{run_date}.json")
    if len(candidates) < 20:
        log("WARNUNG: weniger als 20 Kandidaten. Redaktion nutzt Web-Suche zum Auffüllen.")


if __name__ == "__main__":
    main()
