#!/usr/bin/env python3
"""Schritt 2: Redaktion. Wählt aus den Kandidaten die 15 relevantesten,
duplikatfreien Meldungen, kategorisiert sie (5+4+3+2+1), schreibt Titel und
Kurztexte in DE, EN und ES und erstellt die drei Podcast-Skripte.

Nutzt die Claude API (ANTHROPIC_API_KEY). Bei zu wenigen Kandidaten darf das
Modell per Web-Suche nachrecherchieren, aber nur bei den vier Quellen.

Aufruf: python3 pipeline/edit.py [--date YYYY-MM-DD]
"""
import argparse
import json
import os
import re
import sys
from datetime import date

import anthropic

import config

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")

STYLE = """
Schreibstil (verbindlich für DE, EN und ES):
- Analytisch, ruhig, präzise. Kein Alarmismus, keine Buzzwords, keine Marketingsprache.
- Jede Meldung: Titel (max. 90 Zeichen, informativ, kein Clickbait) und Kurztext mit 2 bis 3 Sätzen
  (45 bis 75 Wörter): erster Satz = was passiert ist, zweiter und dritter Satz = Einordnung und Konsequenz
  für Unternehmen oder Gesellschaft.
- Keine Quellenangaben im Fliesstext (kein "laut Handelsblatt", kein "berichtet TechCrunch"). Die Quelle
  wird separat angezeigt.
- Keine Floskeln wie "Was oft unterschätzt wird", "Das eigentliche Problem ist", "Der entscheidende
  Unterschied liegt in", "hier zeigt sich", "es ist wichtig zu betonen".
- Deutsch: Schweizer Orthografie (ss statt ß, ä ö ü), gerade Anführungszeichen "", keine Gedankenstriche
  in Form von em-dashes, Genderdoppelpunkt wo sinnvoll (Mitarbeitende, Nutzer:innen). "KI" bleibt "KI".
- Englisch: klares internationales Business-Englisch, "AI".
- Spanisch: neutrales Spanisch für ein internationales Publikum, "IA".
- Keine Fakten erfinden. Nur, was aus Titel und Beschreibung der Kandidaten hervorgeht.
"""

PODCAST = """
Podcast-Skripte (je Sprache eines, 2 bis 3 Minuten gesprochen bei Sprechtempo 1.4; das entspricht
520 bis 680 Wörtern Text, Zielwert 600):
- Keine Begrüssung, kein Intro, kein Abschiedsgruss. Erster Satz ist eine konkrete Frage zur
  wichtigsten Meldung der Woche.
- Struktur: Frage als Einstieg, dann die 5 bis 6 wichtigsten Meldungen in einer Argumentationslinie
  (These, Mechanismus, Evidenz, Konsequenz), Übergänge statt Aufzählung, ein pointierter Satz mit
  trockenem Humor ist erlaubt. Schluss: eine verdichtete Kernaussage, kein Fazit-Wort, kein Appell,
  kein Abonnieren-Hinweis.
- Deutsch: "KI" wird als "KI" geschrieben (zwei Buchstaben, wird so gesprochen). Englisch: "AI".
  Spanisch: "IA". Keine Abkürzungen, die eine Sprachsynthese nicht lesen kann, Zahlen ausschreiben,
  wenn sie unter zwanzig sind. Firmennamen normal schreiben.
- Pro Absatz ein Gedanke, 3 bis 5 Sätze. Absätze durch Leerzeilen trennen.
"""


def build_prompt(run_date, candidates, min_candidates):
    cands = "\n".join(
        f"{i+1}. [{c['source']}] {c.get('published','')[:10]} | {c['title']} | {c['url']}\n   {c.get('summary','')[:400]}"
        for i, c in enumerate(candidates))
    cats = "\n".join(f"- {c['key']}: {c['label']['de']} ({c['target']} Meldungen)" for c in config.CATEGORIES)
    search_note = ""
    if len(candidates) < min_candidates:
        from datetime import timedelta
        start = (run_date - timedelta(days=7)).strftime('%d.%m.%Y')
        search_note = (f"\nEs liegen nur {len(candidates)} Kandidaten vor. Recherchiere mit der Web-Suche "
                       f"zusätzliche Meldungen, die zwischen dem {start} und dem {run_date.strftime('%d.%m.%Y')} "
                       "erschienen sind (nichts Neueres), ausschliesslich von t3n.de, heise.de, "
                       "handelsblatt.com und techcrunch.com, und verwende nur vollständige Artikel-URLs, "
                       "nie Übersichts- oder Tag-Seiten.\n")
    return f"""Du bist Redaktor:in des wöchentlichen "KI Power Update" (news.fragroger.ai) von Roger Basler de Roca.
Heute ist der {run_date.strftime('%d.%m.%Y')}. Berücksichtige nur Meldungen der letzten 7 Tage.

Aufgabe:
1. Wähle aus den Kandidaten die 15 relevantesten Meldungen für Unternehmer:innen, Führungskräfte und
   Entscheider:innen. Keine Duplikate: Wenn mehrere Quellen dasselbe Ereignis berichten, nimm die beste
   Quelle einmal. Mindestens zwei verschiedene Quellen pro Kategorie, wo möglich, und alle vier Quellen
   sollen in der Ausgabe vorkommen.
2. Ordne sie exakt so zu:
{cats}
3. Wähle zusätzlich 5 Reserve-Meldungen (verschiedene Kategorien), falls Links bei der Prüfung ausfallen.
4. Schreibe pro Meldung Titel und Kurztext in Deutsch, Englisch und Spanisch.
5. Schreibe drei Podcast-Skripte (de, en, es), inhaltlich gleich, sprachlich eigenständig formuliert.
{search_note}
{STYLE}
{PODCAST}

Kandidaten:
{cands}

Liefere das Ergebnis über das Tool ausgabe_abliefern ab, mit genau dieser Struktur:
{{
  "items": [
    {{"candidate": 3, "category": "news", "url": "...", "source": "t3n",
      "de": {{"title": "...", "summary": "..."}},
      "en": {{"title": "...", "summary": "..."}},
      "es": {{"title": "...", "summary": "..."}}}}
  ],
  "reserves": [ ...gleiches Format, 5 Einträge... ],
  "podcast": {{"de": "...", "en": "...", "es": "..."}},
  "editorial_note": "2 Sätze zur Auswahl dieser Woche (deutsch)"
}}
"items" enthält genau 15 Einträge in der Reihenfolge der Kategorien (news, tools, regulierung, stimmen, business).
"candidate" ist die Nummer aus der Kandidatenliste oder null bei nachrecherchierten Meldungen.
"""


def _extract_json(text):
    text = (text or "").strip()
    # Codefences entfernen, dann das grösste {...}-Objekt nehmen
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else None


_LANG_OBJ = {"type": "object", "properties": {"title": {"type": "string"}, "summary": {"type": "string"}},
             "required": ["title", "summary"]}
_ITEM = {"type": "object",
         "properties": {"candidate": {"type": ["integer", "null"]},
                        "category": {"type": "string", "enum": config.CATEGORY_KEYS},
                        "url": {"type": "string"}, "source": {"type": "string"},
                        "de": _LANG_OBJ, "en": _LANG_OBJ, "es": _LANG_OBJ},
         "required": ["category", "url", "source", "de", "en", "es"]}
EDITION_TOOL = {
    "name": "ausgabe_abliefern",
    "description": "Liefert die fertige Wochenausgabe als strukturierte Daten ab.",
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {"type": "array", "items": _ITEM},
            "reserves": {"type": "array", "items": _ITEM},
            "podcast": {"type": "object",
                        "properties": {"de": {"type": "string"}, "en": {"type": "string"}, "es": {"type": "string"}},
                        "required": ["de", "en", "es"]},
            "editorial_note": {"type": "string"},
        },
        "required": ["items", "reserves", "podcast", "editorial_note"],
    },
}


def call_claude(prompt, allow_search, model=None):
    """Ruft die Claude API auf. Die Ausgabe wird als erzwungener Tool-Aufruf mit JSON-Schema
    abgeholt, damit das JSON garantiert gültig ist (kein Parsen von Fliesstext). Thinking ist
    deaktiviert, damit das Antwortbudget nicht vom Denken aufgebraucht wird (Sonnet 5.5 hatte 24k Tokens nur gedacht)."""
    model = model or MODEL
    headers = {}
    if os.environ.get("ANTHROPIC_WORKSPACE_ID"):
        headers["anthropic-workspace-id"] = os.environ["ANTHROPIC_WORKSPACE_ID"]
    client = anthropic.Anthropic(default_headers=headers or None, max_retries=3, timeout=1200)
    tools = [EDITION_TOOL]
    tool_choice = {"type": "tool", "name": "ausgabe_abliefern"}
    if allow_search:
        tools.append({"type": "web_search_20250305", "name": "web_search", "max_uses": 12})
        tool_choice = {"type": "any"}
    kwargs = dict(model=model, max_tokens=32000,
                  # Erzwungener Tool-Aufruf verträgt sich nicht mit Extended Thinking, darum aus.
                  thinking={"type": "disabled"},
                  system="Du bist Redaktor:in. Du lieferst das Ergebnis ausschliesslich über das Tool "
                         "ausgabe_abliefern ab, nie als Fliesstext.",
                  tools=tools, tool_choice=tool_choice,
                  messages=[{"role": "user", "content": prompt}])
    messages = kwargs["messages"]
    for _round in range(8):
        with client.messages.stream(**kwargs) as stream:
            stream.until_done()
            resp = stream.get_final_message()
        for b in resp.content:
            if getattr(b, "type", "") == "tool_use" and b.name == "ausgabe_abliefern":
                return b.input
        # Web-Suche-Runde (server tool) ohne Abgabe: Verlauf fortsetzen und Abgabe erzwingen
        if resp.stop_reason == "tool_use" or any(getattr(b, "type", "") == "server_tool_use" for b in resp.content):
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": "Liefere jetzt die Ausgabe über das Tool ausgabe_abliefern ab."})
            kwargs["tool_choice"] = {"type": "tool", "name": "ausgabe_abliefern"}
            continue
        types = [getattr(b, "type", "?") for b in resp.content]
        diag = (f"model={resp.model} stop_reason={resp.stop_reason} usage={resp.usage} blocks={types}")
        print("Antwortdiagnose: " + diag, file=sys.stderr)
        raise RuntimeError("Keine Ausgabe über das Tool erhalten (" + diag + ")")
    raise RuntimeError("Keine Ausgabe nach mehreren Runden")


def validate(result):
    items = result["items"]
    assert len(items) == 15, f"{len(items)} statt 15 Meldungen"
    counts = {k: 0 for k in config.CATEGORY_KEYS}
    urls = set()
    for it in items:
        assert it["category"] in counts, f"unbekannte Kategorie {it['category']}"
        counts[it["category"]] += 1
        assert it["url"].startswith("http"), it["url"]
        assert it["url"] not in urls, f"Duplikat {it['url']}"
        urls.add(it["url"])
        for lang in config.LANGS:
            assert it[lang]["title"] and it[lang]["summary"], f"Text fehlt ({lang}) bei {it['url']}"
    targets = {c["key"]: c["target"] for c in config.CATEGORIES}
    assert counts == targets, f"Kategorienverteilung {counts} statt {targets}"
    for lang in config.LANGS:
        words = len(result["podcast"][lang].split())
        assert 450 <= words <= 800, f"Podcast {lang}: {words} Wörter"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--min-candidates", type=int, default=30)
    args = ap.parse_args()
    run_date = date.fromisoformat(args.date)
    candidates = json.loads((config.RESEARCH / f"{run_date}.json").read_text(encoding="utf-8"))
    prompt = build_prompt(run_date, candidates, args.min_candidates)
    last_err = None
    fallback = os.environ.get("CLAUDE_MODEL_FALLBACK", "claude-opus-5-5")
    for attempt in range(4):
        model = MODEL if attempt < 2 else fallback
        print(f"Redaktion, Versuch {attempt+1} mit {model}", file=sys.stderr)
        try:
            result = call_claude(prompt, allow_search=len(candidates) < args.min_candidates, model=model)
            validate(result)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"Versuch {attempt+1} fehlgeschlagen: {e}", file=sys.stderr)
    else:
        raise SystemExit(f"Redaktion fehlgeschlagen: {last_err}")

    by_url = {c["url"]: c for c in candidates}
    for it in result["items"] + result["reserves"]:
        c = by_url.get(it["url"], {})
        it["published"] = (c.get("published") or "")[:10]
        it.setdefault("source", c.get("source", ""))
        it["url_is_article"] = True
    edition = {
        "date": run_date.isoformat(),
        "week": run_date.isocalendar()[1],
        "languages": config.LANGS,
        "editorial_note": result.get("editorial_note", ""),
        "items": result["items"],
        "reserves": result["reserves"],
        "podcast": {lang: {"script": result["podcast"][lang]} for lang in config.LANGS},
        "model": MODEL,
    }
    config.EDITIONS.mkdir(parents=True, exist_ok=True)
    out = config.EDITIONS / f"{run_date}.json"
    out.write_text(json.dumps(edition, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Ausgabe geschrieben: {out}")


if __name__ == "__main__":
    main()
