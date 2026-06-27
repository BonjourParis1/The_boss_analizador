"""
brain/llm.py — Cerebro IA con Claude (SDK oficial de Anthropic).

Usa Claude Opus 4.8 con pensamiento adaptativo para:
  * reason_trade(): explicar/razonar una operación en lenguaje natural a partir del
    contexto técnico (señal, indicadores, velas, noticias).
  * analyze_content(): extraer ideas y sentimiento de trading de un texto
    (artículo, transcripción de YouTube, notas).

Diseño honesto: el LLM RAZONA y EXPLICA el contexto; no inventa precios ni
garantiza resultados. Se le instruye a hablar en probabilidades y riesgo.

Sin ANTHROPIC_API_KEY el módulo queda inactivo (is_available() == False) y la app
funciona igual, solo sin el comentario en lenguaje natural.
"""
from __future__ import annotations

from functools import lru_cache

from config import settings

_SYSTEM = (
    "Eres un analista de trading senior, prudente y honesto. Explicas el contexto "
    "técnico (RSI, MACD, medias, Bollinger, ATR, patrones de velas, soporte/resistencia) "
    "y de noticias en lenguaje claro para un operador que ejecuta manualmente en su bróker. "
    "Hablas SIEMPRE en términos de probabilidad y gestión de riesgo, nunca de certezas ni "
    "de ganancias garantizadas. No inventas datos: te ciñes al contexto que recibes. "
    "Si la señal es débil o contradictoria, lo dices y recomiendas esperar. "
    "Respondes en español, conciso, con: lectura del mercado, escenario probable, "
    "y gestión de riesgo (dónde poner stop/objetivo y por qué). Recuerda al final, en una "
    "línea, que no es asesoramiento financiero."
)


def is_available() -> bool:
    return settings.has_llm


@lru_cache(maxsize=1)
def _client():
    import anthropic
    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


def _complete(system: str, user: str, max_tokens: int = 1400) -> str:
    """Llamada a Claude con streaming (evita timeouts) y pensamiento adaptativo."""
    with _client().messages.stream(
        model=settings.anthropic_model,
        max_tokens=max_tokens,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        msg = stream.get_final_message()
    return "".join(b.text for b in msg.content if b.type == "text").strip()


def reason_trade(sig, symbol_label: str, news_titles: list[str] | None = None) -> str:
    """Devuelve el razonamiento del experto sobre una señal concreta."""
    news = "\n".join(f"- {t}" for t in (news_titles or [])[:6]) or "(sin titulares)"
    ctx = (
        f"Activo: {symbol_label}\n"
        f"Señal del motor: {sig.action} (confianza {sig.confidence}%)\n"
        f"Precio: {sig.price}\nRSI: {sig.rsi}\nATR: {sig.atr}\n"
        f"Tendencia: {sig.trend}\nPatrones de velas: {', '.join(sig.patterns) or 'ninguno'}\n"
        f"Soporte: {sig.support}  Resistencia: {sig.resistance}\n"
        f"Stop sugerido: {sig.stop_loss}  Objetivo: {sig.take_profit}\n"
        f"Sentimiento de noticias: {sig.news_score}\n"
        f"Razones técnicas detectadas:\n- " + "\n- ".join(sig.reasons) + "\n\n"
        f"Titulares recientes:\n{news}\n\n"
        "Explica al operador qué está pasando y qué escenario es más probable, "
        "con su gestión de riesgo. Sé conciso (máx ~180 palabras)."
    )
    return _complete(_SYSTEM, ctx)


_CONTENT_SYSTEM = (
    "Eres un analista que resume contenido de trading (artículos, notas, "
    "transcripciones de video) para extraer lo útil y operable. Devuelves: "
    "1) resumen en 3-5 puntos, 2) sesgo general (alcista/bajista/neutral) con una "
    "frase de justificación, 3) ideas o reglas accionables mencionadas, y 4) banderas "
    "rojas o afirmaciones dudosas (promesas de ganancias, señales infalibles, etc.). "
    "Eres escéptico: marcas el 'humo'. Respondes en español."
)


def analyze_content(text: str, source: str = "") -> str:
    """Resume y evalúa un texto/transcripción aportado por el usuario."""
    text = text.strip()
    if len(text) > 24000:           # recorte defensivo de seguridad
        text = text[:24000] + "\n[...contenido recortado...]"
    user = (f"Fuente: {source or 'desconocida'}\n\nContenido:\n{text}\n\n"
            "Analízalo según tu formato.")
    return _complete(_CONTENT_SYSTEM, user, max_tokens=1600)
