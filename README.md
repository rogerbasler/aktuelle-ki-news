# KI Power Update

Wöchentlicher KI-Nachrichtenüberblick von Roger Basler de Roca (fragRoger) in Partnerschaft mit ki-power.me.
Live: https://news.fragroger.ai (DE) · https://news.fragroger.ai/en/ · https://news.fragroger.ai/es/

Jeden Samstag um 05:00 Uhr (Europe/Zurich) sammelt die Pipeline 40 bis 60 Meldungen der letzten sieben Tage
aus t3n, heise, Handelsblatt und TechCrunch, wählt die 15 relevantesten (5+4+3+2+1 über fünf Rubriken),
schreibt Titel und Kurztexte in DE, EN und ES, prüft jeden Link zweimal, erzeugt drei Podcast-Audios mit
HeyGen (Tempo 1.4) und veröffentlicht die Website über GitHub Pages.

## Aufbau

```
data/editions/YYYY-MM-DD.json   eine Datei pro Ausgabe (Meldungen DE/EN/ES, Podcast-Skripte, Linkprüfung)
data/research/YYYY-MM-DD.{json,md}  Recherche-Rohdaten (40 bis 60 Kandidaten)
data/voices.json                HeyGen-Stimmen pro Sprache ("auto" = aus der Voice Library wählen)
audio/YYYY-MM-DD/podcast-{de,en,es}.mp3
reports/YYYY-MM-DD.md           Run-Report (Auswahl, Linkprüfung, Stimme und Voice-ID, Dauer)
pipeline/                       Python-Skripte (siehe unten)
templates/, assets/             Website-Vorlagen und CSS im fragRoger-CI
.github/workflows/weekly.yml    Zeitplan und Veröffentlichung
```

Generiert (nicht von Hand bearbeiten): `index.html`, `en/`, `es/`, `archiv/`, `suche/`, `impressum/`,
`datenschutz/`, `feed-*.xml`, `podcast-*.xml`, `search-index-*.json`, `sitemap.xml`, `404.html`.

## Pipeline

| Schritt | Skript | Zweck |
|---|---|---|
| 1 | `fetch_sources.py` | Kandidaten aus RSS (Fallback HTML) sammeln, Recherche speichern |
| 2 | `edit.py` | Claude API: Auswahl, Rubriken, Übersetzungen, Podcast-Skripte, 5 Reserven |
| 3 | `verify_links.py` | jede URL zweimal prüfen, Ausfälle durch Reserven ersetzen |
| 4 | `tts.py` | HeyGen v3 Speech API, Chunks, ffmpeg-Concat, Tempo 1.4, Dauerprüfung |
| 5 | `build_site.py` | statische Website in drei Sprachen inkl. Archiv, Suche, Feeds |
| | `run.py --stage full|text-only|audio-only|build-only` | Orchestrierung und Run-Report |

Lokal: `pip install -r pipeline/requirements.txt`, ffmpeg installieren, `ANTHROPIC_API_KEY` und
`HEYGEN_API_KEY` setzen, dann `python3 pipeline/run.py --stage full`.

## Secrets (Repository Settings → Secrets and variables → Actions)

- `ANTHROPIC_API_KEY` (Redaktion und Übersetzung)
- `HEYGEN_API_KEY` (Audio). Fehlt der Key oder antwortet HeyGen nicht, bleibt das bisherige Audio
  unverändert; es gibt keinen Fallback auf eine andere Stimme oder einen anderen Dienst.
- Optional Variable `CLAUDE_MODEL` (Standard `claude-sonnet-5-5`).

## Domain

`CNAME` enthält `news.fragroger.ai`. Im DNS von fragroger.ai muss ein CNAME-Record `news` auf
`rogerbasler.github.io` zeigen. GitHub Pages leitet `rogerbasler.github.io/aktuelle-ki-news/` danach
automatisch auf die Domain um; "Enforce HTTPS" in den Pages-Einstellungen aktivieren, sobald das
Zertifikat ausgestellt ist.

## Stimmen

`data/voices.json` steht auf `auto`: Beim ersten Audio-Lauf filtert `tts.py` die öffentliche HeyGen Voice
Library nach Sprache und Geschlecht (weiblich), listet drei Kandidatinnen mit Voice-ID und Preview-URL im
Run-Report, wählt die erste und schreibt sie in `voices.json`. Soll eine andere Stimme gelten, dort
`{"name": ..., "voice_id": ...}` eintragen. Voice-IDs werden nie erfunden.
