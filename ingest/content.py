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

import requests

from brain import llm
from db import cloud

_YT_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|live/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})")


@dataclass
class Ingested:
    source: str
    kind: str            # "texto" | "youtube"
    text: str            # contenido en crudo (transcripción o texto)
    sentiment: float     # -1..1 (VADER)
    analysis: str        # análisis del experto (modelo local) o aviso si no hay IA
    saved: str = ""      # dónde se guardó el conocimiento ("Supabase"/"local")


def _safe_analysis(text: str, source: str) -> str:
    """Intenta el análisis de la IA; si está al límite, NO bloquea el guardado."""
    if not llm.is_available():
        return ("ℹ️ El cerebro IA no está disponible ahora; se guardó el contenido y su "
                "sentimiento. El análisis completo se hará cuando la IA tenga cuota.")
    try:
        return llm.analyze_content(text, source)
    except Exception as e:  # noqa: BLE001 — sin exponer claves
        return (f"⚠️ La IA está al límite ahora mismo ({e}). El contenido y su "
                "sentimiento SÍ quedaron guardados; el análisis se completará luego.")


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
    """Descarga la transcripción de un video de YouTube de forma ROBUSTA.

    Prueba: idiomas preferidos -> cualquier transcripción manual o automática ->
    traducción a español. Soporta la API clásica y la nueva (1.x).
    """
    vid = youtube_id(url)
    if not vid:
        raise ValueError("URL de YouTube no válida.")
    from youtube_transcript_api import YouTubeTranscriptApi

    def _join(chunks):
        # admite dicts {"text":..} o snippets con .text
        out = []
        for c in chunks:
            out.append(c["text"] if isinstance(c, dict) else getattr(c, "text", ""))
        return " ".join(t for t in out if t).strip()

    # 1) Camino directo con idiomas preferidos (API clásica)
    try:
        return _join(YouTubeTranscriptApi.get_transcript(vid, languages=list(languages)))
    except Exception:
        pass
    # 2) Listar todas y elegir la mejor disponible (manual/auto/traducida)
    try:
        tl = YouTubeTranscriptApi.list_transcripts(vid)
        # idioma preferido
        for lang in languages:
            try:
                return _join(tl.find_transcript([lang]).fetch())
            except Exception:
                pass
        # cualquiera y, si se puede, traducir a español
        for t in tl:
            try:
                if getattr(t, "is_translatable", False):
                    try:
                        return _join(t.translate("es").fetch())
                    except Exception:
                        pass
                return _join(t.fetch())
            except Exception:
                continue
    except Exception:
        pass
    # 3) API nueva (instancia) por si la versión instalada la usa
    try:
        api = YouTubeTranscriptApi()
        return _join(api.fetch(vid, languages=list(languages)))
    except Exception:
        pass
    raise RuntimeError("Este video no tiene transcripción accesible "
                       "(o está restringida). Prueba con otro video.")


def ingest_text(text: str, source: str = "texto pegado") -> Ingested:
    sent = round(_vader(text), 3)
    analysis = _safe_analysis(text, source)
    saved = cloud.knowledge_save("texto", source, sent, analysis, text)
    return Ingested(source, "texto", text, sent, analysis, saved)


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
    resumen_fuentes = "**Fuentes consultadas:**\n\n" + material[:1500]
    out = "ℹ️ Cerebro IA no disponible ahora.\n\n" + resumen_fuentes
    if llm.is_available():
        try:
            out = llm.analyze_content(material, f"Investigación de {symbol.label}")
        except Exception as e:  # noqa: BLE001 — sin exponer claves; mostramos las fuentes
            out = f"⚠️ {e}\n\n{resumen_fuentes}"
    # Guarda el aprendizaje en la nube para que el cerebro lo recuerde
    try:
        cloud.knowledge_save("auto", f"auto:{symbol.label}", _vader(material), out, material)
    except Exception:
        pass
    return out


def ingest_youtube(url: str) -> Ingested:
    text = fetch_youtube_transcript(url)
    sent = round(_vader(text), 3)
    analysis = _safe_analysis(text, f"YouTube: {url}")
    saved = cloud.knowledge_save("youtube", url, sent, analysis, text)
    return Ingested(url, "youtube", text, sent, analysis, saved)
