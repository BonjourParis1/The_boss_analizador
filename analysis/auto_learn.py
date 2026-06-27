"""
analysis/auto_learn.py — Autoaprendizaje a partir del HISTÓRICO (sin que operes).

Idea (aprendizaje auto-supervisado): para cada vela del histórico, calculamos las
features técnicas y miramos qué pasó DESPUÉS (horizonte de N velas). Etiquetamos:
  * SUBE  si el precio sube más de `umbral`,
  * BAJA  si baja más de `umbral`,
  * LATERAL en otro caso.
Entrenamos un clasificador (RandomForest) que aprende a anticipar esa etiqueta a
partir del estado técnico actual. Así el sistema "aprende del mercado" solo, sin
necesidad de que registres operaciones.

Honestidad: esto NO predice el futuro con certeza; estima probabilidades a partir de
patrones pasados, que pueden no repetirse. Se reporta la precisión validada para que
sepas cuánto fiarte.

El modelo se guarda en ml/auto_model.joblib (ignorado por git).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from analysis.indicators import compute_all
from ml.model import FEATURE_NAMES, extract_features

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml" / "auto_model.joblib"
LABELS = ["SUBE", "LATERAL", "BAJA"]


@dataclass
class TrainReport:
    samples: int
    accuracy_cv: float          # precisión validada (0..1)
    horizon: int
    threshold_pct: float
    class_counts: dict
    importances: dict           # importancia de cada feature (0..1)


def _label_forward(df: pd.DataFrame, horizon: int, threshold: float) -> np.ndarray:
    """Etiqueta cada fila por el retorno a `horizon` velas vista."""
    close = df["close"].values
    n = len(close)
    labels = np.empty(n, dtype=object)
    for i in range(n):
        j = i + horizon
        if j >= n:
            labels[i] = None
            continue
        ret = (close[j] - close[i]) / close[i]
        labels[i] = "SUBE" if ret > threshold else "BAJA" if ret < -threshold else "LATERAL"
    return labels


def build_dataset(df_raw: pd.DataFrame, horizon: int = 6, threshold: float = 0.004):
    """Construye (X, y) a partir de un DataFrame OHLCV crudo."""
    df = compute_all(df_raw)
    labels = _label_forward(df, horizon, threshold)
    X, y = [], []
    # Empezamos tras el calentamiento de indicadores (50 = EMA50)
    for i in range(50, len(df) - horizon):
        feats = extract_features(df.iloc[: i + 1])
        X.append(feats[0])
        y.append(labels[i])
    return np.array(X, dtype=float), np.array(y, dtype=object)


def train_from_history(datasets: list[pd.DataFrame], horizon: int = 6,
                       threshold: float = 0.004) -> TrainReport:
    """Entrena con una o varias series históricas (p. ej. varios activos)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import cross_val_score
    import joblib

    Xs, ys = [], []
    for df in datasets:
        try:
            X, y = build_dataset(df, horizon, threshold)
            Xs.append(X)
            ys.append(y)
        except Exception:
            continue
    if not Xs:
        raise RuntimeError("No se pudo construir el dataset (datos insuficientes).")

    X = np.vstack(Xs)
    y = np.concatenate(ys)
    clf = RandomForestClassifier(n_estimators=300, random_state=42,
                                 class_weight="balanced", n_jobs=-1)
    acc = 0.0
    if len(set(y)) > 1 and len(y) >= 50:
        acc = float(cross_val_score(clf, X, y, cv=4).mean())
    clf.fit(X, y)
    joblib.dump({"model": clf, "features": FEATURE_NAMES,
                 "horizon": horizon, "threshold": threshold}, MODEL_PATH)

    counts = {lbl: int(np.sum(y == lbl)) for lbl in LABELS}
    importances = {name: round(float(v), 3)
                   for name, v in zip(FEATURE_NAMES, clf.feature_importances_)}
    return TrainReport(len(y), round(acc, 3), horizon, threshold, counts, importances)


def model_exists() -> bool:
    return MODEL_PATH.exists()


def predict(df_ind: pd.DataFrame):
    """Devuelve (etiqueta, probabilidad%, horizonte) o (None, None, None)."""
    if not MODEL_PATH.exists():
        return None, None, None
    import joblib
    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    X = extract_features(df_ind)
    pred = model.predict(X)[0]
    proba = float(np.max(model.predict_proba(X))) * 100
    return pred, round(proba, 1), bundle.get("horizon", 6)
