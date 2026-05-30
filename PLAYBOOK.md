# KI Power Update – Wöchentlicher Workflow Playbook

Letzte Aktualisierung: 30. Mai 2026

---

## QUELLEN

- t3n.de/tag/kuenstliche-intelligenz
- heise.de/thema/Kuenstliche-Intelligenz
- handelsblatt.com (KI-Briefing)
- techcrunch.com/category/artificial-intelligence

---

## SCHRITT-FÜR-SCHRITT WORKFLOW

### 1. Repository klonen
```bash
git clone https://github.com/rogerbasler/aktuelle-ki-news
```

### 2. News sammeln
News von allen 4 Quellen der letzten 7 Tage sammeln.

### 3. Top 15 auswählen
Top 15 News auswählen, in 5 Kategorien einteilen, alle Titel ins Deutsche übersetzen.

**Kategorien:** 🧠 K.I. News der Woche | 🚀 Tools & Startups | ⚖️ Regulierung & Ethik | 🎙️ Stimmen & Perspektiven | 🏭 Business & Society

### 4. Audio generieren (HeyGen TTS)
- Voice ID: `1803df59c37443789d2e4f71c82859a0`
- Sprache: `de`
- Podcast-Skript ca. 2–3 Min. schreiben
- Skript in Chunks à max. 800 Zeichen aufteilen
- Alle Chunks mit HeyGen TTS via MCP generieren:
```bash
manus-mcp-cli tool call text_to_speech --server heygen \
  -i '{"text": "<CHUNK>", "voice_id": "1803df59c37443789d2e4f71c82859a0", "language": "de"}'
```
- Alle Chunks herunterladen und mit ffmpeg zusammenfügen:
```bash
echo "file 'chunk1.wav'" > concat_list.txt
echo "file 'chunk2.wav'" >> concat_list.txt
# ... weitere Chunks
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy ki_update_podcast.wav -y
```

**FALLBACK falls HeyGen MCP nicht verfügbar:** Google TTS (gtts) verwenden:
```python
from gtts import gTTS
tts = gTTS(text=chunk, lang='de', slow=False)
tts.save('chunk_1.mp3')
```
Dann mit ffmpeg zu ki_update_podcast.mp3 zusammenfügen (kein WAV-Zwischenschritt nötig).

### 5. AUDIO-KONVERTIERUNG – Mobile-Fix (PFLICHT bei HeyGen)

> **Ursache:** HeyGen liefert WAV-Container mit MP3-Inhalt. iOS Safari und Android-Browser können diesen nicht abspielen.

```bash
ffmpeg -i ki_update_podcast.wav -vn -acodec libmp3lame -ab 128k -ar 44100 -ac 1 ki_update_podcast.mp3 -y
```

Der `<audio>`-Tag in der index.html muss **MP3 zuerst** enthalten:
```html
<audio controls style="width: 100%;" preload="metadata">
  <source src="ki_update_podcast.mp3" type="audio/mpeg">
  <source src="ki_update_podcast.wav" type="audio/wav">
  Dein Browser unterstützt das Audio-Element nicht.
</audio>
```

### 6. index.html erstellen
Neue index.html mit aktuellem Datum und allen 15 News erstellen. Struktur der bestehenden index.html beibehalten: Header, Audio-Player, 5 Kategorien, Footer.

### 7. LINK-VALIDIERUNG (vor dem Deploy – PFLICHT)

Jeden einzelnen News-Artikel-Link prüfen:
```bash
curl -s -o /dev/null -w "%{http_code}" -L <URL>
```
- Nur Links mit HTTP-Status **200** verwenden
- Bei Fehler (404, 403 etc.): korrekten Link per Websuche ermitteln oder Artikel weglassen
- Alle Footer-Links MÜSSEN exakt `https://ki-power.me/` lauten – **keine Unterpfade** (kein /kurse, /blog, /podcast etc.)

### 8. Deployment via GitHub API
```
Repo:   rogerbasler/aktuelle-ki-news
Branch: master
Token:  in /home/ubuntu/deploy_to_github.py
```

Dateien deployen: `index.html`, `ki_update_podcast.mp3`, `ki_update_podcast.wav`

Deployment-Skript: `/home/ubuntu/deploy_to_github.py`

### 9. Verifikation
```bash
# MP3 MIME-Type prüfen (muss audio/mp3 oder audio/mpeg sein)
curl -sI https://rogerbasler.github.io/aktuelle-ki-news/ki_update_podcast.mp3 | grep content-type

# Anzahl News-Artikel prüfen (muss 15 ergeben)
curl -s https://rogerbasler.github.io/aktuelle-ki-news/ | grep -c "news-item"
```

---

## BEKANNTE FEHLERQUELLEN & FIXES

| Problem | Ursache | Fix |
|---|---|---|
| Audio auf Mobile stumm | HeyGen WAV = MP3-Stream in WAV-Container | Schritt 5: ffmpeg-Konvertierung zu echtem MP3 |
| Footer-Links broken | Unterpfade wie /kurse, /blog etc. existieren nicht | Alle Footer-Links auf `https://ki-power.me/` setzen |
| News-Link 404 | TechCrunch/t3n ändern URLs | curl-Validierung + Websuche für korrekten Link |
| HeyGen MCP nicht verfügbar | Connector deaktiviert oder Session-Reset | Fallback: gtts (Google TTS) verwenden |
| manus-mcp-cli: unknown flag --params | Falscher Flag | Korrekt: `-i` statt `--params` |

---

## LIVE-URL

[https://rogerbasler.github.io/aktuelle-ki-news/](https://rogerbasler.github.io/aktuelle-ki-news/)
