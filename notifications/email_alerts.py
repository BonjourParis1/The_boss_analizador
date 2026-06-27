"""
notifications/email_alerts.py — Avisos por correo de señales fuertes (SMTP).

DESACTIVADO por defecto. Para activarlo, en tu .env:
    EMAIL_ENABLED=true
    SMTP_USER=tucorreo@gmail.com
    SMTP_PASSWORD=<app password de Gmail>   (NO tu contraseña normal)
    EMAIL_TO=destino@gmail.com

Para Gmail necesitas una "App password":
    https://myaccount.google.com/apppasswords  (requiere verificación en 2 pasos)

Incluye un anti-spam simple: no repite el mismo aviso para el mismo símbolo+acción
dentro de una ventana de tiempo.
"""
from __future__ import annotations

import smtplib
import time
from email.mime.text import MIMEText

from analysis.engine import Signal
from config import settings

_last_sent: dict[str, float] = {}
_COOLDOWN_SECONDS = 600  # no repetir el mismo aviso en 10 minutos


def is_enabled() -> bool:
    return settings.email_enabled and bool(settings.smtp_user and settings.smtp_password
                                           and settings.email_to)


def send_signal_alert(sig: Signal, symbol_label: str) -> tuple[bool, str]:
    """Envía un correo si el aviso está activado y no está en cooldown."""
    if not is_enabled():
        return False, "Correo desactivado (configura EMAIL_ENABLED y credenciales en .env)."

    key = f"{sig.symbol_key}:{sig.action}"
    now = time.time()
    if now - _last_sent.get(key, 0) < _COOLDOWN_SECONDS:
        return False, "Aviso reciente ya enviado (en cooldown)."

    subject = f"[Guía Experto] {sig.icon} {sig.action} {symbol_label} — confianza {sig.confidence:.0f}%"
    body = (
        f"Señal: {sig.action} ({sig.confidence:.0f}% de confianza)\n"
        f"Activo: {symbol_label}\n"
        f"Precio: {sig.price}\n"
        f"Stop Loss: {sig.stop_loss}   Take Profit: {sig.take_profit}\n"
        f"RSI: {sig.rsi}   Noticias: {sig.news_score}\n\n"
        f"Razones:\n- " + "\n- ".join(sig.reasons) +
        "\n\n(Aviso automático. No es asesoramiento financiero.)"
    )
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = settings.email_to

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
        _last_sent[key] = now
        return True, f"Correo enviado a {settings.email_to}."
    except Exception as e:  # noqa: BLE001
        return False, f"Error enviando correo: {e}"
