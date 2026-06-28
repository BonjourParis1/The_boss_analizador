"""
analysis/news.py — Noticias financieras + análisis de sentimiento por símbolo.

Fuentes:
  * NewsAPI (https://newsapi.org) si hay NEWSAPI_KEY -> mejor cobertura.
  * Si no, feeds RSS públicos (Yahoo Finance, Investing) -> sin API key.

Sentimiento: VADER (vaderSentiment), un analizador léxico afinado para textos
financieros/sociales en inglés. Devuelve un score normalizado en [-1, 1].

NOTA honesta: el sentimiento de noticias es una señal de CONTEXTO, no una bola
de cristal. El motor lo usa como factor secundario, nunca como única razón.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import requests

from config import Symbol, settings

_TIMEOUT = 10
_HEADERS = {"User-Agent": "GuiaExpertoTrading/2.0"}


@dataclass
class NewsItem:
    title: str
    source: str
    url: str
    published: str
    sentiment: float  # -1..1


@dataclass
class NewsDigest:
    items: list[NewsItem]
    score: float            # media de sentimiento -1..1
    label: str              # "Positivo" / "Neutral" / "Negativo"

    @property
    def emoji(self) -> str:
        return {"Positivo": "🟢", "Neutral": "⚪", "Negativo": "🔴"}[self.label]


def _analyzer():
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    if not hasattr(_analyzer, "_inst"):
        _analyzer._inst = SentimentIntensityAnalyzer()
    return _analyzer._inst


def _score_text(text: str) -> float:
    return _analyzer().polarity_scores(text or "")["compound"]


def _fetch_newsapi(query: str, limit: int) -> list[NewsItem]:
    r = requests.get("https://newsapi.org/v2/everything", headers=_HEADERS, timeout=_TIMEOUT,
                     params={"q": query, "language": "en", "sortBy": "publishedAt",
                             "pageSize": limit, "apiKey": settings.newsapi_key})
    r.raise_for_status()
    out = []
    for a in r.json().get("articles", [])[:limit]:
        title = a.get("title") or ""
        out.append(NewsItem(title, (a.get("source") or {}).get("name", "NewsAPI"),
                            a.get("url", ""), a.get("publishedAt", ""), _score_text(title)))
    return out


def _fetch_rss(query: str, limit: int) -> list[NewsItem]:
    """Feed RSS de Yahoo Finance (búsqueda). Sin API key."""
    import feedparser
    url = "https://news.google.com/rss/search"
    feed = feedparser.parse(f"{url}?q={requests.utils.quote(query)}&hl=en-US&gl=US&ceid=US:en")
    out = []
    for e in feed.entries[:limit]:
        title = getattr(e, "title", "")
        src = getattr(getattr(e, "source", None), "title", "Google News")
        out.append(NewsItem(title, src, getattr(e, "link", ""),
                            getattr(e, "published", ""), _score_text(title)))
    return out


def _fetch_finnhub(symbol: Symbol, limit: int) -> list[NewsItem]:
    """Noticias financieras reales de Finnhub (fuente fiable, en tiempo real)."""
    from datetime import date, timedelta
    cat = {"cripto": "crypto", "forex": "forex"}.get(symbol.type)
    if symbol.type == "stock":
        to = date.today()
        frm = to - timedelta(days=7)
        r = requests.get("https://finnhub.io/api/v1/company-news", timeout=_TIMEOUT,
                         headers=_HEADERS,
                         params={"symbol": symbol.provider_id, "from": frm.isoformat(),
                                 "to": to.isoformat(), "token": settings.finnhub_api_key})
    else:
        r = requests.get("https://finnhub.io/api/v1/news", timeout=_TIMEOUT, headers=_HEADERS,
                         params={"category": cat or "general", "token": settings.finnhub_api_key})
    r.raise_for_status()
    out = []
    for a in r.json()[:limit]:
        title = a.get("headline") or ""
        if not title:
            continue
        out.append(NewsItem(title, a.get("source", "Finnhub"), a.get("url", ""),
                            str(a.get("datetime", "")), _score_text(title)))
    return out


def get_news(symbol: Symbol, limit: int = 8) -> NewsDigest:
    """Devuelve titulares recientes + sentimiento agregado para el símbolo.

    Orden de fuentes (de más a menos fiable): Finnhub -> NewsAPI -> RSS.
    """
    query = symbol.news_query or symbol.label
    items: list[NewsItem] = []
    if settings.finnhub_api_key:
        try:
            items = _fetch_finnhub(symbol, limit)
        except Exception:
            items = []
    if not items:
        try:
            items = _fetch_newsapi(query, limit) if settings.newsapi_key else _fetch_rss(query, limit)
        except Exception:
            try:
                items = _fetch_rss(query, limit)
            except Exception:
                items = []

    if not items:
        return NewsDigest([], 0.0, "Neutral")

    score = sum(i.sentiment for i in items) / len(items)
    label = "Positivo" if score > 0.08 else "Negativo" if score < -0.08 else "Neutral"
    return NewsDigest(items, round(score, 3), label)
