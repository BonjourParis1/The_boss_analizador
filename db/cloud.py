"""
db/cloud.py — Persistencia en SUPABASE de lo que el sistema aprende.

Guarda en la nube (no en tu PC) dos cosas:
  * knowledge  -> el CONOCIMIENTO que le enseñas (texto/YouTube analizado) y la
                  auto-investigación, para que el cerebro lo recuerde y lo use.
  * signals    -> cada señal y su resultado (acierto/fallo) para medir la precisión.

Si Supabase no está configurado, cae a archivos JSON locales (solo como respaldo).
Usa caché en memoria para no consultar la nube en cada refresco.
"""
from __future__ import annotations

import json
import threading
import time

from config import SECRETS_DIR, settings

_lock = threading.Lock()
_KFILE = SECRETS_DIR / "knowledge.json"
_SFILE = SECRETS_DIR / "signals.json"
_AFILE = SECRETS_DIR / "access_log.json"
_SETFILE = SECRETS_DIR / "app_settings.json"
_cache = {"signals": None, "ts": 0.0}


def _client():
    from db.supabase_store import _client as c
    return c()


def _ljson(p):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _lsave(p, data):
    try:
        p.write_text(json.dumps(data[-1000:]), encoding="utf-8")
    except Exception:
        pass


def where() -> str:
    return "Supabase (nube)" if settings.use_supabase else "archivo local"


# ----------------------- Ajustes del usuario (capital, riesgo) -------------
def _dict_load(p):
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def setting_get(key: str, default=None):
    if settings.use_supabase:
        try:
            r = _client().table("app_settings").select("value").eq("key", key).limit(1).execute()
            if r.data:
                return r.data[0]["value"]
            return default
        except Exception:
            pass
    return _dict_load(_SETFILE).get(key, default)


def setting_set(key: str, value) -> None:
    if settings.use_supabase:
        try:
            _client().table("app_settings").upsert({"key": key, "value": value}).execute()
            return
        except Exception:
            pass
    with _lock:
        d = _dict_load(_SETFILE)
        d[key] = value
        try:
            _SETFILE.write_text(json.dumps(d), encoding="utf-8")
        except Exception:
            pass


# ----------------------- Conocimiento (lo que enseñas) ---------------------
def knowledge_save(kind: str, source: str, sentiment: float, summary: str,
                   content: str = "") -> str:
    row = {"kind": kind, "source": (source or "")[:300], "sentiment": float(sentiment or 0),
           "summary": (summary or "")[:4000], "content": (content or "")[:8000]}
    if settings.use_supabase:
        try:
            _client().table("knowledge").insert(row).execute()
            return "Supabase"
        except Exception:
            pass
    with _lock:
        d = _ljson(_KFILE)
        d.append({**row, "created_at": time.time()})
        _lsave(_KFILE, d)
    return "local"


def knowledge_search(query: str, limit: int = 3) -> list:
    """Busca en lo APRENDIDO las entradas más relevantes a la consulta (sin IA).
    Ranking simple por coincidencia de palabras en resumen/origen."""
    import re
    items = []
    if settings.use_supabase:
        try:
            r = (_client().table("knowledge")
                 .select("kind,source,summary,sentiment,created_at")
                 .order("created_at", desc=True).limit(150).execute())
            items = r.data or []
        except Exception:
            items = []
    else:
        items = list(reversed(_ljson(_KFILE)))[:150]
    words = [w for w in re.findall(r"[a-záéíóúñ0-9]+", (query or "").lower()) if len(w) > 2]
    if not words:
        return []
    scored = []
    for it in items:
        text = ((it.get("summary") or "") + " " + (it.get("source") or "")).lower()
        score = sum(text.count(w) for w in words)
        if score > 0:
            scored.append((score, it))
    scored.sort(key=lambda x: -x[0])
    return [it for _, it in scored[:limit]]


def knowledge_count() -> int:
    if settings.use_supabase:
        try:
            r = _client().table("knowledge").select("id", count="exact").limit(1).execute()
            return int(r.count or 0)
        except Exception:
            pass
    return len(_ljson(_KFILE))


def knowledge_recent(limit: int = 6) -> list:
    if settings.use_supabase:
        try:
            r = (_client().table("knowledge")
                 .select("kind,source,summary,sentiment,created_at")
                 .order("created_at", desc=True).limit(limit).execute())
            return r.data or []
        except Exception:
            pass
    return list(reversed(_ljson(_KFILE)))[:limit]


# --------------------- Señales y resultados (precisión) --------------------
def signal_save(symbol: str, direction: str, expiry_seconds: int,
                entry_price: float, source: str = "auto", features=None) -> None:
    row = {"symbol": symbol, "direction": direction, "expiry_seconds": int(expiry_seconds),
           "entry_price": float(entry_price), "status": "pending", "source": source,
           "entry_ts": time.time()}
    if features is not None:
        row["features"] = list(features)
    if settings.use_supabase:
        try:
            _client().table("signals").insert(row).execute()
            _cache["ts"] = 0.0
            return
        except Exception:
            pass
    with _lock:
        d = _ljson(_SFILE)
        row["id"] = row["entry_ts"]
        d.append(row)
        _lsave(_SFILE, d)
        _cache["ts"] = 0.0


def signals_all(ttl: int = 20) -> list:
    now = time.time()
    if _cache["signals"] is not None and now - _cache["ts"] < ttl:
        return _cache["signals"]
    data = []
    if settings.use_supabase:
        try:
            r = (_client().table("signals").select("*")
                 .order("entry_ts", desc=True).limit(2000).execute())
            data = r.data or []
        except Exception:
            data = []
    else:
        data = _ljson(_SFILE)
    _cache["signals"] = data
    _cache["ts"] = now
    return data


def access_log_save(event: str, detail: str = "") -> None:
    """Registra un evento de acceso (ok / fallo / logout) con su hora."""
    row = {"event": event, "detail": (detail or "")[:200], "ts": time.time()}
    if settings.use_supabase:
        try:
            _client().table("access_log").insert(row).execute()
            return
        except Exception:
            pass
    with _lock:
        d = _ljson(_AFILE)
        d.append(row)
        _lsave(_AFILE, d)


def access_log_recent(limit: int = 12) -> list:
    if settings.use_supabase:
        try:
            r = (_client().table("access_log").select("event,detail,ts")
                 .order("ts", desc=True).limit(limit).execute())
            return r.data or []
        except Exception:
            pass
    return list(reversed(_ljson(_AFILE)))[:limit]


def signal_update(sig_id, status: str, exit_price: float) -> None:
    if settings.use_supabase:
        try:
            _client().table("signals").update(
                {"status": status, "exit_price": float(exit_price)}
            ).eq("id", sig_id).execute()
            _cache["ts"] = 0.0
            return
        except Exception:
            pass
    with _lock:
        d = _ljson(_SFILE)
        for s in d:
            if s.get("id") == sig_id:
                s["status"] = status
                s["exit_price"] = exit_price
        _lsave(_SFILE, d)
        _cache["ts"] = 0.0
