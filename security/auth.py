"""
security/auth.py — Autenticación de administrador con TRIPLE clave.

Protocolo de seguridad aplicado:
  * Tres claves independientes (Clave 1, 2 y 3). Las tres deben ser correctas.
  * Nunca se guardan en texto plano. Se almacena solo el hash con
    PBKDF2-HMAC-SHA256 (260.000 iteraciones) + salt aleatorio de 16 bytes
    distinto por cada clave.  -> resistente a fuerza bruta y rainbow tables.
  * Comparación en tiempo constante (hmac.compare_digest) -> evita timing attacks.
  * Bloqueo temporal tras N intentos fallidos (anti fuerza bruta).
  * Los hashes viven en .secrets/admin_keys.json, que está en .gitignore.

Genera/actualiza las claves con:  python setup_admin.py
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass

from config import ADMIN_KEYS_FILE, settings

# Parámetros del KDF
_ALGO = "sha256"
_ITERATIONS = 260_000
_SALT_BYTES = 16
_NUM_KEYS = 3  # triple clave


# ----------------------------- Hashing ------------------------------------
def hash_password(password: str, salt: bytes | None = None) -> str:
    """Devuelve un hash serializable 'pbkdf2_sha256$iter$salt_b64$hash_b64'."""
    if salt is None:
        salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, _ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        _ITERATIONS,
        base64.b64encode(salt).decode(),
        base64.b64encode(dk).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    """Compara una clave candidata con el hash almacenado (tiempo constante)."""
    try:
        algo, iterations, salt_b64, hash_b64 = stored.split("$")
        assert algo == "pbkdf2_sha256"
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        dk = hashlib.pbkdf2_hmac(_ALGO, password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


# ----------------------- Persistencia de las claves ------------------------
def save_admin_keys(passwords: list[str]) -> None:
    """Guarda los hashes de las 3 claves. Usado por setup_admin.py."""
    if len(passwords) != _NUM_KEYS:
        raise ValueError(f"Se requieren exactamente {_NUM_KEYS} claves.")
    data = {"hashes": [hash_password(p) for p in passwords], "version": 1}
    ADMIN_KEYS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    # Permisos restrictivos donde el SO lo permita (no-op en Windows básico)
    try:
        os.chmod(ADMIN_KEYS_FILE, 0o600)
    except OSError:
        pass


def admin_keys_exist() -> bool:
    return ADMIN_KEYS_FILE.exists()


def _load_hashes() -> list[str]:
    if not admin_keys_exist():
        raise FileNotFoundError(
            "No hay claves configuradas. Ejecuta:  python setup_admin.py"
        )
    data = json.loads(ADMIN_KEYS_FILE.read_text(encoding="utf-8"))
    return data["hashes"]


# ---------------------------- Verificación ---------------------------------
@dataclass
class AuthResult:
    ok: bool
    message: str
    failed_index: int | None = None  # qué clave falló (para feedback genérico)


def verify_triple(key1: str, key2: str, key3: str) -> AuthResult:
    """Valida las tres claves. No revela cuál falló por seguridad."""
    hashes = _load_hashes()
    candidates = [key1, key2, key3]
    all_ok = True
    for cand, stored in zip(candidates, hashes):
        if not verify_password(cand, stored):
            all_ok = False
    if all_ok:
        return AuthResult(True, "Acceso concedido.")
    return AuthResult(False, "Una o más claves son incorrectas.")


# ----------------------- Control de bloqueo (anti fuerza bruta) ------------
class LoginGuard:
    """Lleva la cuenta de intentos fallidos y aplica bloqueo temporal.

    Pensado para guardarse en st.session_state (proceso/sesión Streamlit).
    """

    def __init__(self) -> None:
        self.failed = 0
        self.locked_until = 0.0

    @property
    def is_locked(self) -> bool:
        return time.time() < self.locked_until

    def seconds_left(self) -> int:
        return max(0, int(self.locked_until - time.time()))

    def register_failure(self) -> None:
        self.failed += 1
        if self.failed >= settings.auth_max_attempts:
            self.locked_until = time.time() + settings.auth_lockout_seconds
            self.failed = 0  # reinicia el contador tras bloquear

    def register_success(self) -> None:
        self.failed = 0
        self.locked_until = 0.0
