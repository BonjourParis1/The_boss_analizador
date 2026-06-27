"""
brain/llm.py — Cerebro IA con modelo OPEN-SOURCE LOCAL (gratis, sin API de pago).

Proveedores soportados (LLM_PROVIDER en .env):
  * "ollama" (por defecto): habla con Ollama en http://localhost:11434.
        Instala Ollama (https://ollama.com) y descarga un modelo, p. ej.:
            ollama pull llama3.1
        Configura el modelo con OLLAMA_MODEL (por defecto "llama3.1").
  * "openai_compatible": cualquier servidor local con API estilo OpenAI
        (LM Studio en http://localhost:1234/v1, vLLM, etc.). Usa OPENAI_BASE_URL,
        OPENAI_API_KEY (puede ir vacía en local) y LLM_MODEL.
  * "none": desactiva la IA (la app funciona igual, sin razonamiento en texto).

Todo es local y gratuito; NO se usa ninguna API de pago. Se conversa por HTTP con
`requests` (sin SDKs propietarios). Si el servidor no responde, is_available() == False.

Diseño honesto: el modelo RAZONA y EXPLICA el contexto; no inventa precios ni
garantiza resultados. Se le instruye a hablar en probabilidades y gestión de riesgo.
"""
from __future__ import annotations

import requests

from config import settings

_SYSTEM = (
    "Eres un analista de trading senior, prudente y honesto. Explicas el contexto "
    "técnico (RSI, MACD, medias, Bollinger, ATR, patrones de velas, soporte/resistencia) "
    "y de noticias en lenguaje claro para un operador que ejecuta manualmente. "
    "Hablas SIEMPRE en términos de probabilidad y gestión de riesgo, nunca de certezas "
    "ni de ganancias garantizadas. No inventas datos: te ciñes al contexto recibido. "
    "Si la señal es débil o contradictoria, lo dices y recomiendas esperar. Respondes en "
    "español, conciso, con: lectura del mercado, escenario probable y gestión de riesgo "
    "(stop/objetivo y por qué). Cierra con una línea recordando que no es asesoramiento financiero."
)

_CONTENT_SYSTEM = (
    "Eres un analista que resume contenido de trading (artículos, notas, transcripciones) "
    "para extraer lo útil y operable. Devuelves: 1) resumen en 3-5 puntos, 2) sesgo general "
    "(alcista/bajista/neutral) con una frase, 3) ideas o reglas accionables, y 4) banderas "
    "rojas o afirmaciones dudosas (promesas de ganancias, señales infalibles). Eres escéptico "
    "y marcas el 'humo'. Respondes en español."
)


# ------------------------------ Disponibilidad -----------------------------
def is_available() -> bool:
    """Comprueba si el backend local está accesible (ping corto)."""
    p = settings.llm_provider
    try:
        if p == "ollama":
            r = requests.get(f"{settings.ollama_url}/api/tags", timeout=2)
            return r.ok
        if p == "openai_compatible":
            r = requests.get(f"{settings.openai_base_url}/models", timeout=2,
                             headers=_oai_headers())
            return r.ok
    except Exception:
        return False
    return False


def backend_label() -> str:
    if settings.llm_provider == "ollama":
        return f"Ollama · {settings.llm_model}"
    if settings.llm_provider == "openai_compatible":
        return f"Local OpenAI-compat · {settings.llm_model}"
    return "desactivado"


# --------------------------------- Llamada ---------------------------------
def _oai_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if settings.openai_api_key:
        h["Authorization"] = f"Bearer {settings.openai_api_key}"
    return h


def _chat(system: str, user: str, max_tokens: int = 900) -> str:
    p = settings.llm_provider
    if p == "ollama":
        r = requests.post(
            f"{settings.ollama_url}/api/chat",
            json={
                "model": settings.llm_model,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.4},
            }, timeout=180)
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    if p == "openai_compatible":
        r = requests.post(
            f"{settings.openai_base_url}/chat/completions",
            headers=_oai_headers(),
            json={
                "model": settings.llm_model,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}],
                "max_tokens": max_tokens, "temperature": 0.4, "stream": False,
            }, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    raise RuntimeError("LLM desactivado (LLM_PROVIDER=none).")


# ----------------------------- Funciones de uso ----------------------------
def reason_trade(sig, symbol_label: str, news_titles: list[str] | None = None) -> str:
    news = "\n".join(f"- {t}" for t in (news_titles or [])[:6]) or "(sin titulares)"
    ctx = (
        f"Activo: {symbol_label}\n"
        f"Señal del motor: {sig.action} (confianza {sig.confidence}%)\n"
        f"Precio: {sig.price}\nRSI: {sig.rsi}\nATR: {sig.atr}\n"
        f"Tendencia: {sig.trend}\nPatrones de velas: {', '.join(sig.patterns) or 'ninguno'}\n"
        f"Soporte: {sig.support}  Resistencia: {sig.resistance}\n"
        f"Stop sugerido: {sig.stop_loss}  Objetivo: {sig.take_profit}\n"
        f"Sentimiento de noticias: {sig.news_score}\n"
        f"Razones técnicas:\n- " + "\n- ".join(sig.reasons) + "\n\n"
        f"Titulares recientes:\n{news}\n\n"
        "Explica qué está pasando y qué escenario es más probable, con gestión de "
        "riesgo. Sé conciso (máx ~180 palabras)."
    )
    return _chat(_SYSTEM, ctx)


def analyze_content(text: str, source: str = "") -> str:
    text = text.strip()
    if len(text) > 16000:
        text = text[:16000] + "\n[...recortado...]"
    user = (f"Fuente: {source or 'desconocida'}\n\nContenido:\n{text}\n\n"
            "Analízalo según tu formato.")
    return _chat(_CONTENT_SYSTEM, user, max_tokens=1100)
