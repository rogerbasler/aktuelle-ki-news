#!/usr/bin/env python3
"""Schritt 5: Generiert die statische Website aus data/editions/*.json.

Ausgabe (Repository-Root, wird von GitHub Pages ausgeliefert):
  /                      aktuelle Ausgabe DE          /en/  /es/
  /archiv/               Archivübersicht              /en/archiv/  /es/archiv/
  /archiv/<datum>/       einzelne Ausgabe             /en/archiv/<datum>/ ...
  /suche/                Suche über alle Meldungen    /en/suche/ ...
  /impressum/ /datenschutz/ (+ en, es)
  /search-index-<lang>.json, /feed-<lang>.xml, /podcast-<lang>.xml, /sitemap.xml, /robots.txt, /404.html

Aufruf: python3 pipeline/build_site.py
"""
import json
import re
import shutil
from datetime import date, datetime, timezone
from email.utils import format_datetime
from html import escape
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

import config
import legal
from i18n import STRINGS, MONTHS, format_date

env = Environment(loader=FileSystemLoader(str(config.TEMPLATES)), autoescape=select_autoescape(["html"]))
BUILD_ID = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
OUT = config.ROOT


def load_editions():
    eds = []
    for p in sorted(config.EDITIONS.glob("*.json")):
        e = json.loads(p.read_text(encoding="utf-8"))
        e["_date"] = date.fromisoformat(e["date"])
        for i, it in enumerate(e["items"]):
            it["id"] = f"m{i+1}"
        eds.append(e)
    return sorted(eds, key=lambda e: e["_date"])


def lang_prefix(lang):
    return "" if lang == config.DEFAULT_LANG else f"{lang}/"


def alternates(path_after_prefix):
    return {l: f"{config.SITE_URL}/{lang_prefix(l)}{path_after_prefix}" for l in config.LANGS}


def write(rel, html):
    target = OUT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def text_for(item, lang):
    """Text in gewünschter Sprache, sonst Deutsch (ältere Ausgaben)."""
    return item.get(lang) or item["de"]


def base_ctx(lang, section, path, title, description):
    t = STRINGS[lang]
    depth = (lang_prefix(lang) + path).count("/")
    return dict(t=t, lang=lang, lang_prefix=lang_prefix(lang), root="../" * depth, section=section,
                site_url=config.SITE_URL, canonical=f"{config.SITE_URL}/{lang_prefix(lang)}{path}",
                alternates=alternates(path), page_title=title, page_description=description,
                year=date.today().year, build_id=BUILD_ID)


def render_edition(e, lang, is_latest):
    t = STRINGS[lang]
    date_text = format_date(e["_date"], lang)
    cats = []
    for c in config.CATEGORIES:
        items = []
        for it in e["items"]:
            if it["category"] != c["key"]:
                continue
            tx = text_for(it, lang)
            pub = None
            if it.get("published"):
                try:
                    pub = date.fromisoformat(it["published"][:10])
                except ValueError:
                    pub = None
            items.append({**it, "title": tx["title"], "summary": tx["summary"],
                          "published": pub.isoformat() if pub else "",
                          "published_text": format_date(pub, lang) if pub else ""})
        cats.append({"key": c["key"], "icon": c["icon"], "label": c["label"][lang], "entries": items})
    podcast = e.get("podcast", {}).get(lang) or (e.get("podcast", {}).get("de") if lang == "de" else None)
    if not podcast and lang != "de":
        # Ältere Ausgaben: deutsches Audio anbieten, Skript nur wenn Sprache passt
        de = e.get("podcast", {}).get("de")
        podcast = {"audio": de.get("audio"), "duration_sec": de.get("duration_sec")} if de and de.get("audio") else None
    sources = sorted({it["source"] for it in e["items"]})
    path = "" if is_latest else f"archiv/{e['date']}/"
    title = f"{t['site_title']} · {date_text}" if is_latest else f"{t['site_title']} · {t['archive_badge']} {date_text}"
    first = text_for(e["items"][0], lang)["title"] if e["items"] else ""
    desc = f"{t['meta_description']} {first}"[:300]
    jsonld = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage", "name": title,
        "url": f"{config.SITE_URL}/{lang_prefix(lang)}{path}", "datePublished": e["date"], "inLanguage": t["html_lang"],
        "publisher": {"@type": "Person", "name": "Roger Basler de Roca", "url": "https://fragroger.ai"},
        "mainEntity": {"@type": "ItemList", "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "url": it["url"], "name": text_for(it, lang)["title"]}
            for i, it in enumerate(e["items"])]},
    }, ensure_ascii=False)
    ctx = base_ctx(lang, "current" if is_latest else "archive", path, title, desc)
    ctx.update(edition=e, date_text=date_text, categories=cats, podcast=podcast, is_latest=is_latest,
               sources=sources, jsonld=jsonld)
    html = env.get_template("edition.html").render(ctx)
    write(f"{lang_prefix(lang)}{path}index.html", html)
    if is_latest:
        ctx2 = base_ctx(lang, "archive", f"archiv/{e['date']}/", title, desc)
        ctx2.update(edition=e, date_text=date_text, categories=cats, podcast=podcast, is_latest=False,
                    sources=sources, jsonld=jsonld)
        write(f"{lang_prefix(lang)}archiv/{e['date']}/index.html", env.get_template("edition.html").render(ctx2))


def render_archive(editions, lang):
    t = STRINGS[lang]
    years = {}
    for e in reversed(editions):
        d = e["_date"]
        top = text_for(e["items"][0], lang)["title"] if e["items"] else ""
        years.setdefault(d.year, {}).setdefault(MONTHS[lang][d.month - 1], []).append({
            "date": e["date"], "date_text": format_date(d, lang), "week": e["week"], "count": len(e["items"]),
            "has_audio": bool((e.get("podcast") or {}).get(lang, {}).get("audio") or (e.get("podcast") or {}).get("de", {}).get("audio")),
            "translated": lang in e.get("languages", ["de"]), "top": top,
        })
    ordered = [(y, list(m.items())) for y, m in sorted(years.items(), reverse=True)]
    ctx = base_ctx(lang, "archive", "archiv/", f"{t['archive_title']} · {t['site_title']}", t["archive_intro"])
    ctx.update(years=ordered)
    write(f"{lang_prefix(lang)}archiv/index.html", env.get_template("archive.html").render(ctx))


def render_search(editions, lang):
    t = STRINGS[lang]
    index, sources, years = [], set(), set()
    for e in reversed(editions):
        for it in e["items"]:
            tx = text_for(it, lang)
            index.append({"t": tx["title"], "y": tx["summary"][:320], "u": it["url"], "s": it["source"],
                          "c": it["category"], "d": e["date"],
                          "e": f"../archiv/{e['date']}/#{it['id']}"})
            sources.add(it["source"])
            years.add(e["date"][:4])
    (OUT / f"search-index-{lang}.json").write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    ctx = base_ctx(lang, "search", "suche/", f"{t['search_title']} · {t['site_title']}", t["search_intro"])
    ctx.update(categories=[{"key": c["key"], "icon": c["icon"], "label": c["label"][lang]} for c in config.CATEGORIES],
               sources=sorted(sources), years=sorted(years, reverse=True),
               js_strings=json.dumps({"results": t["search_results"], "none": t["search_none"], "in_edition": t["in_edition"]}, ensure_ascii=False),
               js_cats=json.dumps({c["key"]: f"{c['icon']} {c['label'][lang]}" for c in config.CATEGORIES}, ensure_ascii=False))
    write(f"{lang_prefix(lang)}suche/index.html", env.get_template("search.html").render(ctx))


def render_pages(lang):
    t = STRINGS[lang]
    for kind, slug, heading in (("imprint", "impressum/", t["imprint_title"]), ("privacy", "datenschutz/", t["privacy_title"])):
        ctx = base_ctx(lang, "page", slug, f"{heading} · {t['site_title']}", heading)
        ctx.update(heading=heading, body=legal.render(kind, lang))
        write(f"{lang_prefix(lang)}{slug}index.html", env.get_template("page.html").render(ctx))
    if lang == "de":
        ctx = base_ctx(lang, "page", "404.html", t["not_found_title"], t["not_found_text"])
        ctx.update(heading=t["not_found_title"], body=f"<p>{t['not_found_text']}</p><p><a href='{config.SITE_URL}/'>{t['latest_link']} →</a></p>", root=f"{config.SITE_URL}/")
        write("404.html", env.get_template("page.html").render(ctx))


def rfc2822(d):
    return format_datetime(datetime(d.year, d.month, d.day, 5, 0, tzinfo=timezone.utc))


def render_feeds(editions, lang):
    t = STRINGS[lang]
    recent = list(reversed(editions))[:30]
    items = []
    for e in recent:
        link = f"{config.SITE_URL}/{lang_prefix(lang)}archiv/{e['date']}/"
        body = "".join(f"<p><b>{escape(text_for(it, lang)['title'])}</b> {escape(text_for(it, lang)['summary'])} "
                       f"<a href=\"{escape(it['url'])}\">{escape(it['source'])}</a></p>" for it in e["items"])
        items.append(f"""<item><title>{escape(t['site_title'])} {escape(format_date(e['_date'], lang))}</title>
<link>{link}</link><guid isPermaLink="true">{link}</guid><pubDate>{rfc2822(e['_date'])}</pubDate>
<description><![CDATA[{body}]]></description></item>""")
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>{escape(t['site_title'])} ({lang.upper()})</title><link>{config.SITE_URL}/{lang_prefix(lang)}</link>
<description>{escape(t['meta_description'])}</description><language>{t['html_lang']}</language>
<atom:link href="{config.SITE_URL}/feed-{lang}.xml" rel="self" type="application/rss+xml"/>
{''.join(items)}
</channel></rss>"""
    (OUT / f"feed-{lang}.xml").write_text(rss, encoding="utf-8")

    pod_items = []
    for e in recent:
        pod = (e.get("podcast") or {}).get(lang) or ((e.get("podcast") or {}).get("de") if lang == "de" else None)
        if not pod or not pod.get("audio"):
            continue
        url = f"{config.SITE_URL}/{pod['audio']}"
        size = (config.ROOT / pod["audio"]).stat().st_size if (config.ROOT / pod["audio"]).exists() else 0
        link = f"{config.SITE_URL}/{lang_prefix(lang)}archiv/{e['date']}/"
        summary = escape((pod.get("script") or "")[:400])
        dur = int(pod.get("duration_sec") or 0)
        pod_items.append(f"""<item><title>{escape(t['site_title'])} {escape(format_date(e['_date'], lang))}</title>
<link>{link}</link><guid isPermaLink="false">kipu-{lang}-{e['date']}</guid><pubDate>{rfc2822(e['_date'])}</pubDate>
<description>{summary}</description><enclosure url="{url}" length="{size}" type="audio/mpeg"/>
<itunes:duration>{dur // 60}:{dur % 60:02d}</itunes:duration><itunes:explicit>false</itunes:explicit></item>""")
    podcast = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:atom="http://www.w3.org/2005/Atom"><channel>
<title>{escape(t['site_title'])} Podcast ({lang.upper()})</title><link>{config.SITE_URL}/{lang_prefix(lang)}</link>
<description>{escape(t['podcast_hint'])} {escape(t['meta_description'])}</description><language>{t['html_lang']}</language>
<itunes:author>Roger Basler de Roca</itunes:author><itunes:explicit>false</itunes:explicit>
<itunes:image href="{config.SITE_URL}/assets/podcast-cover.png"/>
<itunes:category text="Technology"/><itunes:category text="News"><itunes:category text="Tech News"/></itunes:category>
<atom:link href="{config.SITE_URL}/podcast-{lang}.xml" rel="self" type="application/rss+xml"/>
{''.join(pod_items)}
</channel></rss>"""
    (OUT / f"podcast-{lang}.xml").write_text(podcast, encoding="utf-8")


def render_sitemap(editions):
    urls = []
    for lang in config.LANGS:
        p = lang_prefix(lang)
        urls += [f"{config.SITE_URL}/{p}", f"{config.SITE_URL}/{p}archiv/", f"{config.SITE_URL}/{p}suche/",
                 f"{config.SITE_URL}/{p}impressum/", f"{config.SITE_URL}/{p}datenschutz/"]
        urls += [f"{config.SITE_URL}/{p}archiv/{e['date']}/" for e in editions]
    body = "".join(f"<url><loc>{u}</loc></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>', encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {config.SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / "CNAME").write_text("news.fragroger.ai\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")


def clean_output():
    """Entfernt generierte Seiten, damit keine verwaisten Dateien bleiben."""
    for sub in ("archiv", "suche", "impressum", "datenschutz", "en", "es"):
        shutil.rmtree(OUT / sub, ignore_errors=True)


def main():
    editions = load_editions()
    if not editions:
        raise SystemExit("keine Ausgaben gefunden")
    clean_output()
    latest = editions[-1]
    for lang in config.LANGS:
        for e in editions:
            render_edition(e, lang, is_latest=(e is latest))
        render_archive(editions, lang)
        render_search(editions, lang)
        render_pages(lang)
        render_feeds(editions, lang)
    render_sitemap(editions)
    print(f"Website gebaut: {len(editions)} Ausgaben, aktuell {latest['date']}, Sprachen {config.LANGS}")


if __name__ == "__main__":
    main()
