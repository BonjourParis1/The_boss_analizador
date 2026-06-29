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
                entry_price: float, source: str = "auto") -> None:
    row = {"symbol": symbol, "direction": direction, "expiry_seconds": int(expiry_seconds),
           "entry_price": float(entry_price), "status": "pending", "source": source,
           "entry_ts": time.time()}
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
