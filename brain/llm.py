"""
brain/llm.py — Cerebro IA con modelo OPEN-SOURCE LOCAL (gratis, sin API de pago).

Proveedores soportados (LLM_PROVIDER en .env), todos GRATIS:
  * "ollama" (por defecto): modelo LOCAL con Ollama en http://localhost:11434.
        Instala Ollama (https://ollama.com) y:  ollama pull llama3.1
  * "gemini": Google Gemini free tier (NUBE, sin instalar nada). Consigue una API
        key gratis en https://aistudio.google.com/apikey y ponla en GEMINI_API_KEY.
        Modelo por defecto: gemini-2.0-flash (rápido y gratuito).
  * "openai_compatible": cualquier servidor con API estilo OpenAI — sirve para
        servidores LOCALES (LM Studio en http://localhost:1234/v1) y también para
        free tiers en la nube como Groq, Together AI, DeepInfra o el endpoint
        OpenAI-compat de Hugging Face. Usa OPENAI_BASE_URL, OPENAI_API_KEY y LLM_MODEL.
  * "none": desactiva la IA (la app funciona igual, sin razonamiento en texto).

NO se usa ninguna API de pago. Se conversa por HTTP con `requests`. Si el backend no
responde o falta la clave, is_available() == False y la app sigue funcionando.

Diseño honesto: el modelo RAZONA y EXPLICA el contexto; no inventa precios ni
garantiza resultados. Se le instruye a hablar en probabilidades y gestión de riesgo.
"""
from __future__ import annotations

import requests

from config import settings

_INDICADORES = (
    "CONOCIMIENTO DE INDICADORES (úsalo para razonar):\n"
    "- RSI(14): impulso. <30 sobreventa (posible rebote al alza), >70 sobrecompra "
    "(posible corrección). Divergencias precio/RSI anticipan giros.\n"
    "- MACD: tendencia/momentum. MACD cruzando por encima de su señal = impulso alcista; "
    "por debajo = bajista. El histograma mide la fuerza.\n"
    "- Medias móviles SMA9/SMA21 y EMA50: tendencia. Cruce de SMA9 sobre SMA21 = señal "
    "alcista (y viceversa). Precio sobre EMA50 = sesgo alcista de fondo.\n"
    "- Bandas de Bollinger(20,2): volatilidad. Tocar/romper la banda inferior puede ser "
    "sobreventa; la superior, sobrecompra; bandas estrechas anticipan movimientos fuertes.\n"
    "- ATR: volatilidad para fijar stop-loss/take-profit (p.ej. 1.5×ATR de stop).\n"
    "- Patrones de velas: martillo/envolvente alcista = posible giro al alza; estrella "
    "fugaz/envolvente bajista = giro a la baja; doji = indecisión.\n"
    "- Soporte/Resistencia: zonas donde el precio suele rebotar/frenarse.\n"
    "- Multi-temporalidad: una señal es MÁS fiable cuando coincide en varias "
    "temporalidades (1m, 15m, 1h, diario). Si el corto plazo y el largo plazo se "
    "contradicen, lo prudente es ESPERAR.\n"
)

_SYSTEM = (
    "Eres un analista de trading senior, prudente y honesto. " + _INDICADORES +
    "\nExplicas el contexto técnico y de noticias en lenguaje claro para un operador que "
    "ejecuta manualmente. Hablas SIEMPRE en términos de probabilidad y gestión de riesgo, "
    "nunca de certezas ni de ganancias garantizadas. REGLA CRÍTICA anti-alucinación: NO "
    "inventes cifras (precios, niveles, RSI, %): usa EXCLUSIVAMENTE los valores numéricos "
    "del contexto recibido; si un dato no está, dilo en vez de estimarlo. "
    "Si las temporalidades se contradicen o la señal es débil, dilo y "
    "recomienda esperar. Respondes en español, conciso, con: lectura del mercado, "
    "escenario probable y gestión de riesgo (stop/objetivo y por qué). Cierra recordando "
    "en una línea que no es asesoramiento financiero."
)

_CONTENT_SYSTEM = (
    "Eres un analista que resume contenido de trading (artículos, notas, transcripciones) "
    "para extraer lo útil y operable. Devuelves: 1) resumen en 3-5 puntos, 2) sesgo general "
    "(alcista/bajista/neutral) con una frase, 3) ideas o reglas accionables, y 4) banderas "
    "rojas o afirmaciones dudosas (promesas de ganancias, señales infalibles). Eres escéptico "
    "y marcas el 'humo'. Respondes en español."
)


# ------------------------------ Disponibilidad -----------------------------
def _gemini_model() -> str:
    m = settings.llm_model
    return m if "gemini" in m.lower() else "gemini-2.0-flash"


def is_available() -> bool:
    """Comprueba si el backend está accesible (ping corto / clave presente)."""
    p = settings.llm_provider
    try:
        if p == "gemini":
            return bool(settings.gemini_api_key)   # evitamos gastar cuota con un ping
        if p == "ollama":
            return requests.get(f"{settings.ollama_url}/api/tags", timeout=2).ok
        if p == "openai_compatible":
            return requests.get(f"{settings.openai_base_url}/models", timeout=2,
                                headers=_oai_headers()).ok
    except Exception:
        return False
    return False


def backend_label() -> str:
    p = settings.llm_provider
    if p == "gemini":
        return f"Gemini (free) · {_gemini_model()}"
    if p == "ollama":
        return f"Ollama · {settings.llm_model}"
    if p == "openai_compatible":
        return f"OpenAI-compat · {settings.llm_model}"
    return "desactivado"


# --------------------------------- Llamada ---------------------------------
def _oai_headers() -> dict:
    h = {"Content-Type": "application/json"}
    if settings.openai_api_key:
        h["Authorization"] = f"Bearer {settings.openai_api_key}"
    return h


def _chat(system: str, user: str, max_tokens: int = 900) -> str:
    try:
        return _chat_raw(system, user, max_tokens)
    except requests.HTTPError as e:  # nunca exponer la URL/clave en el mensaje
        code = e.response.status_code if e.response is not None else "?"
        if code == 429:
            raise RuntimeError("IA: límite de peticiones alcanzado, espera un momento.")
        raise RuntimeError(f"IA no disponible (HTTP {code}).")
    except requests.RequestException:
        raise RuntimeError("IA no disponible (problema de red).")


def _chat_raw(system: str, user: str, max_tokens: int = 900) -> str:
    p = settings.llm_provider
    if p == "gemini":
        model = _gemini_model()
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{model}:generateContent?key={settings.gemini_api_key}")
        r = requests.post(url, timeout=120, json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.4},
        })
        r.raise_for_status()
        cands = r.json().get("candidates", [])
        if not cands:
            raise RuntimeError("Gemini no devolvió respuesta (¿filtro de seguridad o cuota?).")
        parts = cands[0].get("content", {}).get("parts", [])
        return "".join(pt.get("text", "") for pt in parts).strip()

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
