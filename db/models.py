"""
db/models.py — Modelos ORM (SQLAlchemy 2.0).

Tablas:
  * recommendations -> cada señal generada por el motor.
  * user_decisions  -> la acción que TÚ tomaste frente a una recomendación.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    action: Mapped[str] = mapped_column(String(10))      # COMPRA/VENTA/MANTENER
    confidence: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    rsi: Mapped[float] = mapped_column(Float, nullable=True)
    atr: Mapped[float] = mapped_column(Float, nullable=True)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=True)
    take_profit: Mapped[float] = mapped_column(Float, nullable=True)
    news_score: Mapped[float] = mapped_column(Float, nullable=True)
    reasons: Mapped[str] = mapped_column(Text, nullable=True)

    decisions: Mapped[list["UserDecision"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan"
    )


class UserDecision(Base):
    __tablename__ = "user_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    recommendation_id: Mapped[int] = mapped_column(ForeignKey("recommendations.id"))
    symbol: Mapped[str] = mapped_column(String(20), index=True)
    user_action: Mapped[str] = mapped_column(String(10))   # lo que hiciste
    bot_action: Mapped[str] = mapped_column(String(10))    # lo que sugirió el bot
    price_at_decision: Mapped[float] = mapped_column(Float)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    # Resultado para estadística de acierto (se rellena al evaluar más tarde)
    outcome: Mapped[str] = mapped_column(String(15), nullable=True)  # acierto/fallo/pendiente

    recommendation: Mapped["Recommendation"] = relationship(back_populates="decisions")
