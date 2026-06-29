"""
analysis/self_learn.py — Autoaprendizaje a partir de RESULTADOS REALES.

El sistema registra cada señal con una "foto" de sus indicadores (features) y, al
vencer la duración, la marca ACIERTO/FALLO comparando con el precio real. Aquí
entrenamos un clasificador que aprende, de esos resultados, qué combinaciones de
indicadores tienden a ACERTAR. Devuelve la probabilidad de acierto de una señal
actual, que se usa para ajustar la confianza del plan.

Los datos viven en Supabase (tabla signals) -> el aprendizaje PERSISTE en la nube.
El modelo se reentrena en memoria cuando hay datos nuevos suficientes (barato).

Honestidad: estima probabilidades a partir de tu historial; no garantiza aciertos.
Necesita un mínimo de resultados para ser fiable.
"""
from __future__ import annotations

from db import cloud
from ml.model import FEATURE_NAMES

MIN_SAMPLES = 30          # mínimo de resultados para entrenar algo fiable
_RETRAIN_STEP = 8         # reentrena cuando hay +N resultados nuevos

_MODEL = None
_TRAINED_N = 0
_LAST_ACC = 0.0


def _resolved_with_features() -> tuple[list, list]:
    """X (features) e y (1=acierto, 0=fallo) de las señales resueltas con foto."""
    X, y = [], []
    for s in cloud.signals_all():
        f = s.get("features")
        if s.get("status") in ("win", "loss") and isinstance(f, (list, tuple)) \
                and len(f) == len(FEATURE_NAMES):
            try:
                X.append([float(v) for v in f])
                y.append(1 if s["status"] == "win" else 0)
            except Exception:
                continue
    return X, y


def stats() -> dict:
    X, y = _resolved_with_features()
    n = len(y)
    wins = sum(y)
    return {"n": n, "wins": wins, "losses": n - wins,
            "win_rate": round(100 * wins / n, 1) if n else 0.0,
            "trained_n": _TRAINED_N, "accuracy": round(100 * _LAST_ACC, 1)}


def train() -> dict:
    """Entrena el modelo con los resultados reales. Devuelve un reporte."""
    global _MODEL, _TRAINED_N, _LAST_ACC
    X, y = _resolved_with_features()
    if len(y) < MIN_SAMPLES or len(set(y)) < 2:
        return {"ok": False, "n": len(y),
                "msg": f"Faltan resultados: {len(y)}/{MIN_SAMPLES} (y ambos: acierto y fallo)."}
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    import numpy as np

    Xa, ya = np.array(X, dtype=float), np.array(y, dtype=int)
    clf = RandomForestClassifier(n_estimators=200, random_state=42,
                                 class_weight="balanced", n_jobs=-1)
    acc = 0.0
    if len(ya) >= 40:
        try:
            acc = float(cross_val_score(clf, Xa, ya, cv=4).mean())
        except Exception:
            acc = 0.0
    clf.fit(Xa, ya)
    _MODEL, _TRAINED_N, _LAST_ACC = clf, len(ya), acc
    importances = {n: round(float(v), 3)
                   for n, v in zip(FEATURE_NAMES, clf.feature_importances_)}
    return {"ok": True, "n": len(ya), "accuracy": round(acc, 3),
            "win_rate": round(100 * int(ya.sum()) / len(ya), 1),
            "importances": importances}


def _maybe_autotrain() -> None:
    """Entrena/reentrena solo cuando hay suficientes datos nuevos (sin bloquear)."""
    X, y = _resolved_with_features()
    if len(y) >= MIN_SAMPLES and (_MODEL is None or len(y) >= _TRAINED_N + _RETRAIN_STEP):
        try:
            train()
        except Exception:
            pass


def win_probability(features) -> float | None:
    """Probabilidad (0..100) de que una señal con estos indicadores ACIERTE.
    None si aún no hay modelo entrenado (datos insuficientes)."""
    _maybe_autotrain()
    if _MODEL is None or features is None:
        return None
    try:
        import numpy as np
        x = np.array([list(features)], dtype=float)
        classes = list(_MODEL.classes_)
        proba = _MODEL.predict_proba(x)[0]
        if 1 in classes:
            return round(100 * float(proba[classes.index(1)]), 1)
    except Exception:
        return None
    return None


def is_ready() -> bool:
    return _MODEL is not None
