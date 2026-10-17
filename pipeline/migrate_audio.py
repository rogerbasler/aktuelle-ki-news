#!/usr/bin/env python3
"""Einmalige Migration: holt alle historischen Podcast-MP3s und -Skripte aus
der Git-Historie und ordnet sie den Ausgaben unter data/editions/ zu.
Audio landet unter audio/<datum>/podcast-de.mp3 (Blobs sind in Git bereits
vorhanden, es entsteht keine zusätzliche Repository-Grösse).
"""
import json
import re
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EDITIONS = ROOT / "data" / "editions"
AUDIO = ROOT / "audio"
MONTHS = {"dec": 12, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6}


def git(*args, binary=False):
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True)
    return r.stdout if binary else r.stdout.decode()


def editions():
    return sorted(date.fromisoformat(p.stem) for p in EDITIONS.glob("*.json"))


def nearest_edition(d, eds):
    cands = [e for e in eds if abs((e - d).days) <= 3]
    if not cands:
        return None
    return min(cands, key=lambda e: (abs((e - d).days), e < d))


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


def main():
    eds = editions()
    assigned = {}
    for line in git("log", "--format=%h %cI", "--", "ki_update_podcast.mp3").strip().splitlines():
        commit, iso = line.split(" ", 1)
        d = datetime.fromisoformat(iso).date()
        ed = nearest_edition(d, eds)
        if not ed or ed in assigned:
            continue
        data = git("show", f"{commit}:ki_update_podcast.mp3", binary=True)
        if len(data) < 100_000:
            continue
        out = AUDIO / ed.isoformat()
        out.mkdir(parents=True, exist_ok=True)
        target = out / "podcast-de.mp3"
        target.write_bytes(data)
        assigned[ed] = target
        print(f"{ed}: audio aus {commit} ({len(data)//1024} KB, {duration(target):.0f} s)")
    # Skripte
    scripts = {}
    for line in git("log", "--format=%h %cI", "--name-only", "--", "podcast_script*.txt").splitlines():
        pass
    for p in ROOT.glob("podcast_script*.txt"):
        m = re.search(r"_(dec|feb|mar|apr|may|jun)(\d{2})", p.name)
        if m:
            mon, day = MONTHS[m.group(1)], int(m.group(2))
            year = 2025 if mon == 12 else 2026
            d = date(year, mon, day)
        else:
            iso = git("log", "-1", "--format=%cI", "--", p.name).strip()
            d = datetime.fromisoformat(iso).date()
        ed = nearest_edition(d, eds)
        if ed:
            scripts[ed] = p.read_text(encoding="utf-8").strip()
    for ed in eds:
        path = EDITIONS / f"{ed}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        pod = data.setdefault("podcast", {}).setdefault("de", {})
        if ed in assigned:
            pod["audio"] = f"audio/{ed}/podcast-de.mp3"
            pod["duration_sec"] = round(duration(assigned[ed]))
        if ed in scripts:
            pod["script"] = scripts[ed]
        if not pod:
            data["podcast"].pop("de", None)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(assigned)} Audios, {len(scripts)} Skripte zugeordnet")


if __name__ == "__main__":
    main()
