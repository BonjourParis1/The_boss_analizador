"""
db/store.py — Selector de backend de persistencia.

Si SUPABASE_URL + SUPABASE_SERVICE_KEY están configurados en .env  -> Supabase.
En caso contrario  -> SQLite local (fallback, para poder probar sin nube).

El resto del proyecto importa SIEMPRE desde aquí, no de los módulos concretos:
    from db.store import save_recommendation, save_user_decision, ...
"""
from __future__ import annotations

from config import settings

if settings.use_supabase:
    from db import supabase_store as _backend
    BACKEND = "Supabase"
else:
    from db import database as _backend
    BACKEND = "SQLite (local)"

# Re-exportamos la interfaz común
init_db = _backend.init_db
save_recommendation = _backend.save_recommendation
save_user_decision = _backend.save_user_decision
get_history = _backend.get_history
get_stats = _backend.get_stats
