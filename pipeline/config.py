"""Zentrale Konfiguration der KI-News-Pipeline."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EDITIONS = DATA / "editions"
RESEARCH = DATA / "research"
REPORTS = ROOT / "reports"
AUDIO = ROOT / "audio"
TEMPLATES = ROOT / "templates"

SITE_URL = "https://news.fragroger.ai"
SITE_NAME = "KI Power Update"
BRAND = "fragRoger"
BRAND_URL = "https://fragroger.ai"
PARTNER_URL = "https://ki-power.me"

LANGS = ["de", "en", "es"]
DEFAULT_LANG = "de"

# Kategorien mit Zielverteilung 5+4+3+2+1 (= 15 Meldungen)
CATEGORIES = [
    {"key": "news", "icon": "🧠", "target": 5,
     "label": {"de": "KI News der Woche", "en": "AI News of the Week", "es": "Noticias de IA de la semana"}},
    {"key": "tools", "icon": "🚀", "target": 4,
     "label": {"de": "Tools & Startups", "en": "Tools & Startups", "es": "Herramientas y startups"}},
    {"key": "regulierung", "icon": "⚖️", "target": 3,
     "label": {"de": "Regulierung & Ethik", "en": "Regulation & Ethics", "es": "Regulación y ética"}},
    {"key": "stimmen", "icon": "🎙️", "target": 2,
     "label": {"de": "Stimmen & Perspektiven", "en": "Voices & Perspectives", "es": "Voces y perspectivas"}},
    {"key": "business", "icon": "🏭", "target": 1,
     "label": {"de": "Business & Society", "en": "Business & Society", "es": "Negocios y sociedad"}},
]
CATEGORY_KEYS = [c["key"] for c in CATEGORIES]

# Quellen: pro Quelle mehrere Feed-Kandidaten plus HTML-Fallback.
SOURCES = [
    {
        "name": "t3n",
        "feeds": ["https://t3n.de/tag/kuenstliche-intelligenz/rss.xml", "https://t3n.de/rss.xml"],
        "html": "https://t3n.de/tag/kuenstliche-intelligenz/",
        "article_pattern": r"https://t3n\.de/news/[a-z0-9-]+-\d+/?$",
        "ai_filter": True,
    },
    {
        "name": "heise",
        "feeds": ["https://www.heise.de/rss/heise-atom.xml", "https://www.heise.de/rss/heise.rdf"],
        "html": "https://www.heise.de/thema/Kuenstliche-Intelligenz",
        "article_pattern": r"https://www\.heise\.de/(news|hintergrund|meinung)/[A-Za-z0-9-]+-\d+\.html$",
        "ai_filter": True,
    },
    {
        "name": "Handelsblatt",
        "feeds": ["https://www.handelsblatt.com/contentexport/feed/schlagzeilen"],
        "html": "https://www.handelsblatt.com/technik/ki/",
        "article_pattern": r"https://www\.handelsblatt\.com/[a-z0-9/-]+/\d{9}\.html$",
        "ai_filter": True,
    },
    {
        "name": "TechCrunch",
        "feeds": ["https://techcrunch.com/category/artificial-intelligence/feed/"],
        "html": "https://techcrunch.com/category/artificial-intelligence/",
        "article_pattern": r"https://techcrunch\.com/\d{4}/\d{2}/\d{2}/[a-z0-9-]+/?$",
        "ai_filter": False,
    },
]

AI_KEYWORDS = ["ki", "k.i.", "künstliche intelligenz", "kuenstliche intelligenz", "ai", "llm", "chatgpt",
               "openai", "anthropic", "claude", "gemini", "mistral", "deepseek", "nvidia", "agent",
               "sprachmodell", "machine learning", "deep learning", "robot", "gpt", "copilot", "ai act"]

# Podcast
PODCAST_TARGET_SECONDS = (120, 180)
PODCAST_SPEED = 1.4
TTS_CHUNK_CHARS = 1500

USER_AGENT = "Mozilla/5.0 (compatible; KI-Power-Update/2.0; +https://news.fragroger.ai)"
