"""Instagram-Stories (1080x1920) aus einer Ausgabe erzeugen, im fragRoger Editorial-Collage-Stil.

Sieben Slides: Cover, je die Top-Meldung der fünf Rubriken, Abschluss mit Verweis auf news.fragroger.ai.
Ausgabe: stories/YYYY-MM-DD/story-01.png ... story-07.png plus stories.zip

Aufruf: python3 pipeline/stories.py --date YYYY-MM-DD
Benötigt: pip install playwright && python -m playwright install chromium
"""
import argparse
import datetime as dt
import html
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"

RUBRIKEN = [
    ("news", "News"),
    ("tools", "Tools"),
    ("regulierung", "Regulierung"),
    ("stimmen", "Stimmen"),
    ("business", "Business"),
]
MONATE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]

CSS = """
@font-face { font-family: Anton; src: url('{fonts}/anton-latin-400-normal.woff2'); }
@font-face { font-family: Marker; src: url('{fonts}/permanent-marker-latin-400-normal.woff2'); }
@font-face { font-family: Inter; font-weight: 400; src: url('{fonts}/inter-latin-400-normal.woff2'); }
@font-face { font-family: Inter; font-weight: 600; src: url('{fonts}/inter-latin-600-normal.woff2'); }
@font-face { font-family: Inter; font-weight: 800; src: url('{fonts}/inter-latin-800-normal.woff2'); }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1920px; }
body {
  font-family: Inter, sans-serif; color: #111; overflow: hidden; position: relative;
  background: #f4efe6;
  background-image:
    radial-gradient(circle at 20% 15%, rgba(0,0,0,.035) 0 1px, transparent 2px),
    radial-gradient(circle at 70% 60%, rgba(0,0,0,.03) 0 1px, transparent 2px);
  background-size: 7px 7px, 11px 11px;
}
.tear { position: absolute; left: -40px; right: -40px; background: #1f3fbf; }
.tear.top { top: 0; height: 330px; clip-path: polygon(0 0,100% 0,100% 78%,93% 86%,85% 79%,76% 90%,66% 81%,55% 92%,44% 82%,33% 91%,22% 80%,12% 89%,0 81%); }
.tear.bottom { bottom: 0; height: 260px; background: #111; clip-path: polygon(0 22%,9% 12%,19% 24%,30% 10%,41% 21%,52% 9%,63% 22%,74% 11%,85% 23%,95% 13%,100% 20%,100% 100%,0 100%); }
.brand { position: absolute; top: 120px; left: 80px; right: 80px; display: flex; justify-content: space-between; align-items: baseline; color: #fff; }
.brand .name { font-family: Anton; font-size: 54px; letter-spacing: 2px; }
.brand .kw { font-family: Inter; font-weight: 800; font-size: 30px; letter-spacing: 3px; }
.foot { position: absolute; bottom: 90px; left: 80px; right: 80px; color: #fff; display: flex; justify-content: space-between; font-weight: 600; font-size: 28px; letter-spacing: 1px; }
.foot b { color: #EA3891; }
.content { position: absolute; top: 470px; left: 80px; right: 80px; }
.label { display: inline-block; background: #C0286E; color: #fff; font-family: Anton; font-size: 46px; letter-spacing: 3px; padding: 10px 28px 6px; transform: rotate(-2deg); text-transform: uppercase; }
.count { font-family: Marker; font-size: 44px; color: #1f3fbf; margin-left: 24px; vertical-align: middle; }
h1 { font-family: Anton; font-weight: 400; color: #111; text-transform: uppercase; line-height: 1.2; margin-top: 54px; }
.summary { margin-top: 48px; font-size: 40px; line-height: 1.38; color: #222; border-left: 10px solid #1f3fbf; padding-left: 32px; }
.source { margin-top: 44px; font-weight: 800; font-size: 28px; letter-spacing: 4px; text-transform: uppercase; color: #555; }
.marker { font-family: Marker; color: #C0286E; }
.tape { position: absolute; width: 230px; height: 64px; background: rgba(234,56,145,.28); transform: rotate(-8deg); }
.big { font-family: Anton; text-transform: uppercase; line-height: 1.12; }
.hl { background: linear-gradient(transparent 58%, rgba(192,40,110,.35) 58%); }
.url { display: inline-block; margin-top: 40px; background: #111; color: #fff; font-family: Anton; font-size: 68px; letter-spacing: 2px; padding: 18px 36px 12px; transform: rotate(1.5deg); }
"""


def date_de(d):
    return f"{d.day}. {MONATE[d.month - 1]} {d.year}"


def first_sentences(text, n=2, limit=260):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = " ".join(parts[:n])
    if len(out) > limit and n > 1:
        out = parts[0]
    return out


def title_size(title):
    n = len(title)
    if n <= 40:
        return 118
    if n <= 60:
        return 100
    if n <= 80:
        return 88
    return 76


def page(body, kw):
    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>{CSS.replace('{fonts}', FONTS.as_uri())}</style></head>
<body><div class="tear top"></div><div class="brand"><span class="name">KI POWER UPDATE</span><span class="kw">KW {kw}</span></div>
{body}
<div class="tear bottom"></div><div class="foot"><span><b>#fragRoger</b> · news.fragroger.ai</span><span>mit ki-power.me</span></div></body></html>"""


def build_slides(ed):
    d = dt.date.fromisoformat(ed["date"])
    kw = ed.get("week") or d.isocalendar()[1]
    items = ed["items"]
    slides = []

    slides.append(page(f"""
<div class="tape" style="top:470px;left:640px"></div>
<div class="content" style="top:520px">
  <div class="marker" style="font-size:64px;transform:rotate(-3deg)">Deine KI-Woche</div>
  <div class="big" style="font-size:210px;margin-top:30px">Was <span class="hl">zählt.</span></div>
  <div class="big" style="font-size:96px;margin-top:40px;color:#1f3fbf">5 Meldungen<br>in 60 Sekunden</div>
  <div class="summary" style="margin-top:70px">{len(items)} Meldungen aus t3n, heise, Handelsblatt und TechCrunch, eingeordnet für Unternehmer:innen.</div>
  <div class="source">{date_de(d)}</div>
</div>""", kw))

    for idx, (key, label) in enumerate(RUBRIKEN, 1):
        it = next((i for i in items if i.get("category") == key), None)
        if not it:
            continue
        t = it["de"]["title"]
        slides.append(page(f"""
<div class="content">
  <span class="label">{label}</span><span class="count">{idx:02d}/05</span>
  <h1 style="font-size:{title_size(t)}px">{html.escape(t)}</h1>
  <div class="summary">{html.escape(first_sentences(it['de']['summary']))}</div>
  <div class="source">Quelle: {html.escape(it['source'])}</div>
</div>""", kw))

    slides.append(page(f"""
<div class="tape" style="top:500px;left:90px;transform:rotate(6deg)"></div>
<div class="content" style="top:560px">
  <div class="marker" style="font-size:60px">Mehr davon?</div>
  <div class="big" style="font-size:150px;margin-top:24px">Alle {len(items)}<br><span class="hl">Meldungen</span></div>
  <div class="big" style="font-size:84px;margin-top:36px;color:#1f3fbf">+ Podcast in 2 Minuten<br>DE · EN · ES</div>
  <div class="url">news.fragroger.ai</div>
  <div class="summary" style="margin-top:70px;font-size:36px">Jeden Samstag neu. Link-Sticker hier setzen.</div>
</div>""", kw))
    return slides


def render(date_str):
    ed = json.loads((ROOT / "data" / "editions" / f"{date_str}.json").read_text(encoding="utf-8"))
    out = ROOT / "stories" / date_str
    out.mkdir(parents=True, exist_ok=True)
    from playwright.sync_api import sync_playwright
    files = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        for n, markup in enumerate(build_slides(ed), 1):
            tmp = out / f"_slide-{n:02d}.html"
            tmp.write_text(markup, encoding="utf-8")
            pg.goto(tmp.as_uri())
            pg.wait_for_timeout(300)
            f = out / f"story-{n:02d}.png"
            pg.screenshot(path=str(f))
            tmp.unlink()
            files.append(f)
        browser.close()
    with zipfile.ZipFile(out / f"ki-power-update-stories-{date_str}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f.name)
    print(f"{len(files)} Stories in {out}")
    return files


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    render(ap.parse_args().date)
