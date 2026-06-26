"""
setup_admin.py — Configura (o cambia) las TRES claves de administrador.

Uso interactivo (recomendado, no muestra las claves en pantalla):
    python setup_admin.py

Uso no interactivo (por ejemplo para sembrar claves automáticamente):
    python setup_admin.py --keys "Clave1" "Clave2" "Clave3"

Las claves se guardan HASHEADAS (PBKDF2-HMAC-SHA256) en .secrets/admin_keys.json,
que está en .gitignore. NUNCA se almacenan en texto plano ni se suben al repo.
"""
from __future__ import annotations

import argparse
import getpass
import sys

# En consolas Windows (cp1252) la salida con emojis falla; forzamos UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from security.auth import save_admin_keys

MIN_LEN = 10


def _validate(p: str, idx: int) -> None:
    if len(p) < MIN_LEN:
        raise SystemExit(f"❌ La clave {idx} debe tener al menos {MIN_LEN} caracteres.")
    if p.isdigit() or p.isalpha():
        raise SystemExit(f"❌ La clave {idx} debe combinar letras, números y símbolos.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Configura las 3 claves de admin.")
    parser.add_argument("--keys", nargs=3, metavar=("K1", "K2", "K3"),
                        help="Las tres claves (modo no interactivo).")
    args = parser.parse_args()

    if args.keys:
        keys = args.keys
    else:
        print("== Configuración de TRIPLE clave de administrador ==")
        print(f"(mínimo {MIN_LEN} caracteres, mezcla de letras/números/símbolos)\n")
        keys = []
        for i in range(1, 4):
            k1 = getpass.getpass(f"Introduce la clave {i}: ")
            k2 = getpass.getpass(f"Repite la clave {i}: ")
            if k1 != k2:
                raise SystemExit(f"❌ Las claves {i} no coinciden.")
            keys.append(k1)

    for i, k in enumerate(keys, 1):
        _validate(k, i)

    if len(set(keys)) < 3:
        raise SystemExit("❌ Las tres claves deben ser distintas entre sí.")

    save_admin_keys(keys)
    print("\n✅ Claves guardadas correctamente (hasheadas) en .secrets/admin_keys.json")
    print("   Ya puedes iniciar el dashboard:  streamlit run app.py")


if __name__ == "__main__":
    sys.exit(main())
