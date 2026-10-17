#!/usr/bin/env python3
"""Schritt 4: Podcast-Audio mit HeyGen (v3 Speech API) für DE, EN und ES.

- Stimme pro Sprache aus data/voices.json. Steht dort "auto", wird die
  öffentliche HeyGen Voice Library nach Sprache, Geschlecht (weiblich) und
  Stil gefiltert; die Kandidatinnen (Name, Voice-ID, Preview-URL) werden im
  Run-Report dokumentiert. Es wird nie eine Voice-ID erfunden.
- Skript wird in Chunks geteilt, jeder Chunk mit speed=1.4 generiert,
  Teile werden mit ffmpeg zusammengefügt, Dauer wird geprüft.
- Ohne HEYGEN_API_KEY oder bei API-Fehlern bleibt das bisherige Audio
  unverändert; die Ursache wird im Report dokumentiert (kein Fallback auf
  eine andere Stimme oder einen anderen Dienst).

Aufruf: python3 pipeline/tts.py [--date YYYY-MM-DD] [--langs de,en,es]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

import requests

import config

API = "https://api.heygen.com/v3"
LANG_NAMES = {"de": ["German", "Deutsch", "Multilingual"], "en": ["English", "Multilingual"],
              "es": ["Spanish", "Español", "Multilingual"]}
VOICES_FILE = config.DATA / "voices.json"
EXCLUDE_NAMES = ["lea"]  # bisherige Stimme "Lea inside sitting" wird ersetzt


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def headers():
    key = os.environ.get("HEYGEN_API_KEY")
    if not key:
        raise RuntimeError("HEYGEN_API_KEY fehlt")
    return {"x-api-key": key, "Content-Type": "application/json"}


def list_voices(lang):
    voices, token = [], None
    for name in LANG_NAMES[lang]:
        token = None
        while True:
            params = {"type": "public", "gender": "female", "language": name, "limit": 100}
            if token:
                params["token"] = token
            r = requests.get(f"{API}/voices", headers=headers(), params=params, timeout=30)
            if r.status_code != 200:
                log(f"  Voice-Liste {name}: HTTP {r.status_code} {r.text[:200]}")
                break
            data = r.json()
            voices += data.get("data", [])
            token = data.get("next_token")
            if not data.get("has_more") or not token:
                break
    uniq = {v["voice_id"]: v for v in voices}
    return list(uniq.values())


def pick_voice(lang, report):
    cfg = json.loads(VOICES_FILE.read_text(encoding="utf-8")) if VOICES_FILE.exists() else {}
    chosen = cfg.get(lang)
    if chosen and chosen != "auto" and chosen.get("voice_id"):
        report.append(f"- {lang}: konfigurierte Stimme {chosen.get('name')} ({chosen['voice_id']})")
        return chosen
    voices = list_voices(lang)
    cands = [v for v in voices if not any(x in v["name"].lower() for x in EXCLUDE_NAMES)]
    # Stil-Filter: energisch, klar, natürlich. Namen mit diesen Hinweisen zuerst.
    style_words = ["energetic", "energisch", "natural", "clear", "news", "professional", "multilingual",
                   "lively", "confident", "friendly"]
    cands.sort(key=lambda v: (-sum(w in (v["name"] + " " + v.get("language", "")).lower() for w in style_words),
                              v["name"]))
    top = cands[:3]
    report.append(f"- {lang}: {len(cands)} weibliche öffentliche Stimmen gefunden; vorgehörte Kandidatinnen:")
    for v in top:
        report.append(f"  - {v['name']} | {v['voice_id']} | {v.get('language')} | Preview: {v.get('preview_audio_url')}")
    if not top:
        raise RuntimeError(f"keine passende Stimme für {lang}")
    voice = {"name": top[0]["name"], "voice_id": top[0]["voice_id"], "language": top[0].get("language")}
    report.append(f"- {lang}: gewählt {voice['name']} ({voice['voice_id']})")
    cfg[lang] = voice
    VOICES_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return voice


def chunk_script(text, limit=config.TTS_CHUNK_CHARS):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if len(cur) + len(p) + 2 > limit and cur:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks


def synth(text, voice_id, lang, out_path):
    body = {"text": text, "voice_id": voice_id, "speed": config.PODCAST_SPEED, "language": lang}
    for attempt in range(4):
        r = requests.post(f"{API}/voices/speech", headers=headers(), json=body, timeout=180)
        if r.status_code == 200:
            url = r.json()["data"]["audio_url"]
            audio = requests.get(url, timeout=120)
            audio.raise_for_status()
            out_path.write_bytes(audio.content)
            return r.json()["data"]
        if r.status_code == 429:
            time.sleep(int(r.headers.get("Retry-After", "10")))
            continue
        if r.status_code in (502, 504):
            time.sleep(5)
            continue
        raise RuntimeError(f"HeyGen HTTP {r.status_code}: {r.text[:300]}")
    raise RuntimeError("HeyGen: zu viele Fehlversuche")


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                          "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip() or 0)


def concat(parts, out):
    lst = out.parent / "concat.txt"
    lst.write_text("\n".join(f"file '{p.name}'" for p in parts), encoding="utf-8")
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-vn", "-acodec",
                    "libmp3lame", "-ab", "128k", "-ar", "44100", "-ac", "1", str(out)],
                   check=True, capture_output=True)
    lst.unlink()
    for p in parts:
        p.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--langs", default=",".join(config.LANGS))
    args = ap.parse_args()
    path = config.EDITIONS / f"{args.date}.json"
    edition = json.loads(path.read_text(encoding="utf-8"))
    report = [f"## Audio ({args.date})", f"Sprechgeschwindigkeit: {config.PODCAST_SPEED} (HeyGen speed-Parameter)"]
    out_dir = config.AUDIO / args.date
    out_dir.mkdir(parents=True, exist_ok=True)
    ok_all = True
    for lang in args.langs.split(","):
        script = edition["podcast"].get(lang, {}).get("script")
        if not script:
            report.append(f"- {lang}: kein Skript vorhanden")
            continue
        try:
            voice = pick_voice(lang, report)
            parts = []
            for i, chunk in enumerate(chunk_script(script)):
                p = out_dir / f"part-{lang}-{i:02d}.mp3"
                synth(chunk, voice["voice_id"], lang, p)
                parts.append(p)
                time.sleep(0.5)
            final = out_dir / f"podcast-{lang}.mp3"
            concat(parts, final)
            secs = duration(final)
            edition["podcast"][lang].update({
                "audio": f"audio/{args.date}/podcast-{lang}.mp3", "duration_sec": round(secs),
                "voice": voice, "speed": config.PODCAST_SPEED, "engine": "HeyGen v3",
            })
            report.append(f"- {lang}: {len(parts)} Chunks, Dauer {secs:.0f} s, Datei {final.name}")
            if not (115 <= secs <= 200):
                report.append(f"  WARNUNG: Dauer ausserhalb 2 bis 3 Minuten (plus Toleranz)")
        except Exception as e:  # noqa: BLE001
            ok_all = False
            report.append(f"- {lang}: FEHLER, bisheriges Audio bleibt unverändert: {e}")
            log(f"{lang}: {e}")
    if "de" in edition["podcast"] and edition["podcast"]["de"].get("audio"):
        # Rückwärtskompatibel: alter Dateiname bleibt erreichbar
        src = config.ROOT / edition["podcast"]["de"]["audio"]
        (config.ROOT / "ki_update_podcast.mp3").write_bytes(src.read_bytes())
    edition.setdefault("reports", {})["audio"] = "\n".join(report)
    path.write_text(json.dumps(edition, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(report))
    if not ok_all:
        sys.exit(2)


if __name__ == "__main__":
    main()
