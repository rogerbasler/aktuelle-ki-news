#!/usr/bin/env python3
"""Orchestrierung des wöchentlichen Laufs.

Stufen (--stage):
  full        fetch -> edit -> verify -> tts -> build -> report   (Standard, samstags 05:00)
  audio-only  tts -> build -> report  (Audio für eine bestehende Ausgabe nachziehen)
  build-only  build -> report         (nur Website neu generieren)
  text-only   fetch -> edit -> verify -> build -> report (ohne Audio)

Aufruf: python3 pipeline/run.py --stage full [--date YYYY-MM-DD]
"""
import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

import config

HERE = Path(__file__).resolve().parent


def step(name, *args, allow_fail=False):
    print(f"\n=== {name} ===", flush=True)
    r = subprocess.run([sys.executable, str(HERE / f"{name}.py"), *args])
    if r.returncode != 0 and not allow_fail:
        raise SystemExit(f"Schritt {name} fehlgeschlagen ({r.returncode})")
    return r.returncode


def report(run_date, stage, audio_rc):
    path = config.EDITIONS / f"{run_date}.json"
    if not path.exists():
        return
    e = json.loads(path.read_text(encoding="utf-8"))
    lines = [f"# Run-Report {run_date} ({stage})", ""]
    lines.append(f"- Sichtbare Meldungen: {len(e['items'])} (Soll 15)")
    counts = {}
    for it in e["items"]:
        counts[it["category"]] = counts.get(it["category"], 0) + 1
    lines.append(f"- Kategorien: {counts}")
    lines.append(f"- Quellen: {sorted({it['source'] for it in e['items']})}")
    lines.append(f"- Sprachen: {e.get('languages')}, Modell: {e.get('model', 'n/a')}")
    lc = e.get("link_check")
    if lc:
        bad = [r for r in lc["results"] if not r["ok"]]
        lines.append(f"- Linkprüfung: {len(lc['results'])} Prüfungen (je 2 Abrufe), {len(bad)} ausgefallen")
        for r in lc["results"]:
            lines.append(f"  - {'OK ' if r['ok'] else 'FEHLER'} {r['status']} {r['url']}")
    lines.append("")
    lines.append(e.get("reports", {}).get("audio", "## Audio\nkein Audio-Schritt in diesem Lauf"))
    if audio_rc not in (0, None):
        lines.append("\nAudio-Schritt mit Fehlern beendet, bisheriges Audio bleibt unverändert.")
    for lang in config.LANGS:
        pod = e.get("podcast", {}).get(lang, {})
        if pod.get("voice"):
            lines.append(f"- Stimme {lang}: {pod['voice'].get('name')} (Voice-ID {pod['voice'].get('voice_id')}), "
                         f"Geschwindigkeit {pod.get('speed')}, Dauer {pod.get('duration_sec')} s")
    config.REPORTS.mkdir(exist_ok=True)
    out = config.REPORTS / f"{run_date}.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="full", choices=["full", "audio-only", "build-only", "text-only"])
    ap.add_argument("--date", default=date.today().isoformat())
    args = ap.parse_args()
    d = args.date
    audio_rc = None
    if args.stage in ("full", "text-only"):
        step("fetch_sources", "--date", d)
        step("edit", "--date", d)
        step("verify_links", "--date", d)
    if args.stage in ("full", "audio-only"):
        audio_rc = step("tts", "--date", d, allow_fail=True)
    step("build_site")
    report(d, args.stage, audio_rc)


if __name__ == "__main__":
    main()
