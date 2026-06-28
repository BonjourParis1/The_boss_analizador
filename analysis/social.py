"""
analysis/social.py — Sentimiento social / de mercado en tiempo real.

Fuentes:
  * Cripto: Fear & Greed Index de alternative.me (GRATIS, sin clave) — mide el
    sentimiento del mercado cripto (miedo extremo ↔ codicia extrema).
  * Opcional (cualquier activo): LunarCrush si defines LUNARCRUSH_API_KEY.

Devuelve un SocialSentiment con score normalizado en [-1, 1] (negativo=miedo,
positivo=codicia/optimismo) para fusionarlo con el sentimiento de noticias y dar
contexto al motor y al cerebro IA. Evita comprar algo "técnicamente barato" que el
mercado real está abandonando.
"""
from __future__ import annotations

from dataclasses import dataclass

import requests

from config import Symbol, settings

_TIMEOUT = 8
_HEADERS = {"User-Agent": "GuiaExpertoTrading/2.0"}


@dataclass
class SocialSentiment:
    score: float          # -1..1
    label: str            # texto legible
    source: str           # de dónde viene
    detail: str = ""

    @property
    def emoji(self) -> str:
        return "🟢" if self.score > 0.12 else "🔴" if self.score < -0.12 else "⚪"


def _fear_greed() -> SocialSentiment | None:
    """Índice de miedo/codicia de cripto (0=miedo extremo, 100=codicia extrema)."""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=1",
                         headers=_HEADERS, timeout=_TIMEOUT)
        r.raise_for_status()
        d = r.json()["data"][0]
        val = int(d["value"])
        score = (val - 50) / 50.0
        return SocialSentiment(round(score, 3), d.get("value_classification", ""),
                               "Fear & Greed (cripto)", f"índice {val}/100")
    except Exception:
        return None


def _lunarcrush(symbol: Symbol) -> SocialSentiment | None:
    if not settings.lunarcrush_api_key:
        return None
    try:
        base = symbol.provider_id.replace("USDT", "").replace("/", "")
        r = requests.get(f"https://lunarcrush.com/api4/public/coins/{base}/v1",
                         headers={**_HEADERS, "Authorization": f"Bearer {settings.lunarcrush_api_key}"},
                         timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json().get("data", {})
        gs = data.get("galaxy_score")  # 0..100
        if gs is None:
            return None
        return SocialSentiment(round((float(gs) - 50) / 50.0, 3),
                               f"Galaxy Score {gs:.0f}", "LunarCrush")
    except Exception:
        return None


def market_sentiment(symbol: Symbol) -> SocialSentiment | None:
    """Sentimiento social/de mercado para el símbolo (None si no hay fuente)."""
    if symbol.type == "cripto":
        return _lunarcrush(symbol) or _fear_greed()
    return _lunarcrush(symbol)
