"""
db/database.py — Inicialización de la base de datos y operaciones de alto nivel.

Usa SQLite por defecto (settings.database_url). Cambia a PostgreSQL solo
ajustando DATABASE_URL en el .env, sin tocar el código.
"""
from __future__ import annotations

import json

import pandas as pd
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from analysis.engine import Signal
from config import settings
from db.models import Base, Recommendation, UserDecision

# `check_same_thread` solo aplica a SQLite (necesario con Streamlit multihilo)
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)


def init_db() -> None:
    """Crea las tablas si no existen."""
    Base.metadata.create_all(engine)


def save_recommendation(sig: Signal) -> int:
    """Persiste una recomendación y devuelve su id."""
    with SessionLocal() as s:  # type: Session
        rec = Recommendation(
            symbol=sig.symbol_key,
            action=sig.action,
            confidence=sig.confidence,
            price=sig.price,
            rsi=sig.rsi,
            atr=sig.atr,
            stop_loss=sig.stop_loss,
            take_profit=sig.take_profit,
            news_score=getattr(sig, "news_score", None),
            reasons=json.dumps(sig.reasons, ensure_ascii=False),
        )
        s.add(rec)
        s.commit()
        return rec.id


def save_user_decision(recommendation_id: int, symbol: str, user_action: str,
                       bot_action: str, price: float, note: str = "") -> int:
    """Guarda la decisión tomada por el usuario frente a una recomendación."""
    with SessionLocal() as s:
        dec = UserDecision(
            recommendation_id=recommendation_id,
            symbol=symbol,
            user_action=user_action,
            bot_action=bot_action,
            price_at_decision=price,
            note=note,
            outcome="pendiente",
        )
        s.add(dec)
        s.commit()
        return dec.id


def get_history(limit: int = 200) -> pd.DataFrame:
    """Devuelve el historial de decisiones unido con su recomendación."""
    with SessionLocal() as s:
        stmt = select(UserDecision).order_by(UserDecision.created_at.desc()).limit(limit)
        rows = s.scalars(stmt).all()
        data = [{
            "fecha": d.created_at,
            "símbolo": d.symbol,
            "mi_decisión": d.user_action,
            "sugerencia_bot": d.bot_action,
            "coincide": "✅" if d.user_action == d.bot_action else "❌",
            "precio": d.price_at_decision,
            "resultado": d.outcome,
            "nota": d.note or "",
        } for d in rows]
    return pd.DataFrame(data)


def get_stats() -> dict:
    """Estadísticas: nº de decisiones, % de coincidencia con el bot, etc."""
    with SessionLocal() as s:
        total = s.scalar(select(func.count(UserDecision.id))) or 0
        recs = s.scalar(select(func.count(Recommendation.id))) or 0
        match = s.scalar(
            select(func.count(UserDecision.id))
            .where(UserDecision.user_action == UserDecision.bot_action)
        ) or 0
    return {
        "recomendaciones_generadas": recs,
        "decisiones_registradas": total,
        "coincidencias_con_bot": match,
        "tasa_coincidencia_pct": round(100 * match / total, 1) if total else 0.0,
    }
