"""
ingest/content.py — Ingesta de contenido que TÚ aportas.

* Texto pegado (artículos, notas de estrategia).
* URL de YouTube -> baja la transcripción (lo que se DICE en el video).

Luego el cerebro IA (brain.llm.analyze_content, modelo local open-source) extrae
resumen, sesgo, ideas accionables y banderas rojas. También calculamos un sentimiento
rápido con VADER para tener una señal aunque el modelo local no esté disponible.

Nota honesta: NO "vemos" el video; analizamos su transcripción de texto. Si el video
no tiene subtítulos/transcripción disponible, no se puede procesar.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from brain import llm

_YT_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|live/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})")


@dataclass
class Ingested:
    source: str
    kind: str            # "texto" | "youtube"
    text: str            # contenido en crudo (transcripción o texto)
    sentiment: float     # -1..1 (VADER)
    analysis: str        # análisis del experto (modelo local) o aviso si no hay IA


def _vader(text: str) -> float:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        return SentimentIntensityAnalyzer().polarity_scores(text[:5000])["compound"]
    except Exception:
        return 0.0


def youtube_id(url: str) -> str | None:
    m = _YT_RE.search(url or "")
    return m.group(1) if m else None


def fetch_youtube_transcript(url: str, languages=("es", "en")) -> str:
    """Descarga la transcripción de un video de YouTube."""
    vid = youtube_id(url)
    if not vid:
        raise ValueError("URL de YouTube no válida.")
    from youtube_transcript_api import YouTubeTranscriptApi
    chunks = YouTubeTranscriptApi.get_transcript(vid, languages=list(languages))
    return " ".join(c["text"] for c in chunks)


def ingest_text(text: str, source: str = "texto pegado") -> Ingested:
    analysis = (llm.analyze_content(text, source) if llm.is_available()
                else "ℹ️ El cerebro IA no está disponible ahora; se muestra solo el "
                     "sentimiento. (Análisis completo cuando la IA esté activa.)")
    return Ingested(source, "texto", text, round(_vader(text), 3), analysis)


def youtube_search(query: str, max_results: int = 3) -> list[dict]:
    """Busca videos recientes en YouTube (requiere YOUTUBE_API_KEY). Lista de {title,url}."""
    from config import settings
    if not settings.youtube_api_key:
        return []
    r = requests.get("https://www.googleapis.com/youtube/v3/search", timeout=10,
                     params={"part": "snippet", "q": query, "type": "video",
                             "order": "relevance", "relevanceLanguage": "es",
                             "maxResults": max_results, "key": settings.youtube_api_key})
    r.raise_for_status()
    out = []
    for it in r.json().get("items", []):
        vid = it.get("id", {}).get("videoId")
        if vid:
            out.append({"title": it["snippet"]["title"],
                        "url": f"https://youtu.be/{vid}"})
    return out


def auto_research(symbol) -> str:
    """Investigación automática: noticias + (si hay clave) un video de YouTube,
    sintetizado por el cerebro IA. Devuelve un informe breve en texto."""
    from analysis.news import get_news
    bits = []
    try:
        dg = get_news(symbol, limit=6)
        bits.append("Titulares recientes (" + dg.label + f", {dg.score:+.2f}):\n" +
                    "\n".join(f"- {i.title}" for i in dg.items[:6]))
    except Exception:
        pass
    # Video de YouTube (opcional)
    try:
        vids = youtube_search(f"trading {symbol.label} análisis hoy")
        if vids:
            tr = fetch_youtube_transcript(vids[0]["url"])
            bits.append(f"Transcripción de '{vids[0]['title']}':\n{tr[:6000]}")
    except Exception:
        pass
    material = "\n\n".join(bits) or "Sin material disponible."
    if llm.is_available():
        return llm.analyze_content(material, f"Investigación de {symbol.label}")
    return ("ℹ️ Cerebro IA no disponible; resumen de fuentes:\n\n" + material[:1500])


def ingest_youtube(url: str) -> Ingested:
    text = fetch_youtube_transcript(url)
    analysis = (llm.analyze_content(text, f"YouTube: {url}") if llm.is_available()
                else "ℹ️ El cerebro IA no está disponible ahora; se muestra solo el "
                     "sentimiento de la transcripción.")
    return Ingested(url, "youtube", text, round(_vader(text), 3), analysis)
