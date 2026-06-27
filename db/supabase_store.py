"""
db/supabase_store.py — Backend de persistencia sobre Supabase (API REST).

Usa el cliente oficial `supabase` con la service_role key (solo en el servidor).
Expone la misma interfaz que db/database.py para que el resto del código no
dependa del backend concreto.

Las tablas deben crearse antes con db/supabase_schema.sql (SQL Editor de Supabase).
"""
from __future__ import annotations

import json
from functools import lru_cache

import pandas as pd

from analysis.engine import Signal
from config import settings


@lru_cache(maxsize=1)
def _client():
    from supabase import create_client
    return create_client(settings.supabase_url, settings.supabase_service_key)


def init_db() -> None:
    """No crea tablas (eso se hace con el SQL). Verifica conectividad."""
    try:
        _client().table("recommendations").select("id").limit(1).execute()
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(
            "No se pudo conectar a Supabase o faltan las tablas. "
            "Ejecuta db/supabase_schema.sql en el SQL Editor. Detalle: " + str(e)
        )


def save_recommendation(sig: Signal) -> int:
    row = {
        "symbol": sig.symbol_key,
        "action": sig.action,
        "confidence": sig.confidence,
        "price": sig.price,
        "rsi": sig.rsi,
        "atr": sig.atr,
        "stop_loss": sig.stop_loss,
        "take_profit": sig.take_profit,
        "news_score": getattr(sig, "news_score", None),
        "reasons": sig.reasons,
    }
    res = _client().table("recommendations").insert(row).execute()
    return res.data[0]["id"]


def save_user_decision(recommendation_id: int, symbol: str, user_action: str,
                       bot_action: str, price: float, note: str = "") -> int:
    row = {
        "recommendation_id": recommendation_id,
        "symbol": symbol,
        "user_action": user_action,
        "bot_action": bot_action,
        "price_at_decision": price,
        "note": note,
        "outcome": "pendiente",
    }
    res = _client().table("user_decisions").insert(row).execute()
    return res.data[0]["id"]


def get_history(limit: int = 200) -> pd.DataFrame:
    res = (_client().table("user_decisions")
           .select("*").order("created_at", desc=True).limit(limit).execute())
    rows = res.data or []
    data = [{
        "fecha": r["created_at"],
        "símbolo": r["symbol"],
        "mi_decisión": r["user_action"],
        "sugerencia_bot": r["bot_action"],
        "coincide": "✅" if r["user_action"] == r["bot_action"] else "❌",
        "precio": r["price_at_decision"],
        "resultado": r.get("outcome"),
        "nota": r.get("note") or "",
    } for r in rows]
    return pd.DataFrame(data)


def get_stats() -> dict:
    cli = _client()
    recs = cli.table("recommendations").select("id", count="exact").limit(1).execute().count or 0
    decs = cli.table("user_decisions").select("*").execute().data or []
    total = len(decs)
    match = sum(1 for d in decs if d["user_action"] == d["bot_action"])
    return {
        "recomendaciones_generadas": recs,
        "decisiones_registradas": total,
        "coincidencias_con_bot": match,
        "tasa_coincidencia_pct": round(100 * match / total, 1) if total else 0.0,
    }
