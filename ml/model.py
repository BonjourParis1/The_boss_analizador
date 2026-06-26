"""
ml/model.py — Modelo supervisado que aprende de TUS decisiones.

Idea: cada vez que registras una decisión, guardamos los indicadores técnicos
del momento + tu acción. Con suficientes ejemplos entrenamos un clasificador
(RandomForest) que predice qué harías TÚ ante un estado de mercado dado.

Features:  rsi, macd_hist, sma_fast-sma_slow, %B de Bollinger, atr_norm.
Target:    tu acción (COMPRA / VENTA / MANTENER).

El modelo se guarda en ml/decision_model.joblib (ignorado por git).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

MODEL_PATH = Path(__file__).resolve().parent / "decision_model.joblib"
FEATURE_NAMES = ["rsi", "macd_hist", "ma_diff", "bb_pctb", "atr_norm"]


def extract_features(df_ind: pd.DataFrame) -> np.ndarray:
    """Convierte la última fila de indicadores en el vector de features del modelo."""
    last = df_ind.iloc[-1]
    price = float(last["close"]) or 1.0
    bb_range = float(last["bb_upper"] - last["bb_lower"]) or 1.0
    feats = [
        float(last["rsi"]),
        float(last["macd_hist"]),
        float(last["sma_fast"] - last["sma_slow"]) / price,
        float(last["close"] - last["bb_lower"]) / bb_range,  # %B
        float(last["atr"]) / price,
    ]
    return np.array(feats, dtype=float).reshape(1, -1)


def train(X: np.ndarray, y: list[str]):
    """Entrena y persiste el clasificador. Devuelve (modelo, accuracy_cv)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    import joblib

    clf = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    score = 0.0
    if len(set(y)) > 1 and len(y) >= 10:
        score = float(cross_val_score(clf, X, y, cv=min(5, len(y) // 2)).mean())
    clf.fit(X, y)
    joblib.dump({"model": clf, "features": FEATURE_NAMES}, MODEL_PATH)
    return clf, score


def load():
    """Carga el modelo entrenado, o None si aún no existe."""
    if not MODEL_PATH.exists():
        return None
    import joblib
    return joblib.load(MODEL_PATH)["model"]


def predict(df_ind: pd.DataFrame):
    """Devuelve (accion_predicha, probabilidad) o (None, None) si no hay modelo."""
    model = load()
    if model is None:
        return None, None
    X = extract_features(df_ind)
    pred = model.predict(X)[0]
    proba = float(np.max(model.predict_proba(X)))
    return pred, round(proba * 100, 1)


def model_exists() -> bool:
    return MODEL_PATH.exists()
