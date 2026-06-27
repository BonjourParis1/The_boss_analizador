# 📊 Guía Experto de Trading

Terminal profesional de análisis y recomendaciones de trading **en tiempo real**,
con estética tipo TradingView / IQ Option. Analiza Forex, criptomonedas, acciones,
índices y commodities; combina **análisis técnico + sentimiento de noticias + un
modelo que aprende de tus decisiones**, y te entrega señales claras
(**📈 Compra / 📉 Venta / ⏸ Mantener**) que replicas manualmente en tu bróker.

> ⚠️ **Aviso honesto e importante**: esto es una herramienta de **apoyo a la
> decisión**, no asesoramiento financiero. **Ningún sistema predice el mercado de
> forma fiable.** Las señales son probabilísticas; el sentimiento de noticias es
> contexto, no una bola de cristal. Operar conlleva riesgo de pérdida. Las
> decisiones —y la responsabilidad— son siempre tuyas.

---

## 🗂️ Estructura

```
THE_BOSS_ANALIZADOR/
├── app.py                  # Terminal Streamlit en tiempo real (entrada)
├── config.py               # Configuración y catálogo de mercados
├── setup_admin.py          # Crea/cambia las 3 claves de administrador
├── requirements.txt
├── .env.example            # Plantilla de variables (segura, sí va a git)
├── .gitignore
│
├── data/                   # APIs reales (Binance, Alpha Vantage, Yahoo Finance)
├── analysis/               # indicators, engine (motor), news (sentimiento), backtest
├── db/                     # store (selector) · supabase_store · database (SQLite)
│   └── supabase_schema.sql #   SQL para crear las tablas en Supabase
├── ml/                     # Modelo que aprende de tus decisiones
├── notifications/          # Avisos por correo (SMTP, desactivado por defecto)
├── security/               # Login de triple clave (PBKDF2 + bloqueo)
└── ui/                     # theme · components (gráficos pro) · auth_ui
```

---

## 🚀 Puesta en marcha

### 1. Instalar (Python 3.11+)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar `.env`
Copia la plantilla y rellena **tus** valores (este archivo NO se sube a git):
```powershell
copy .env.example .env
```
- `SUPABASE_URL` y `SUPABASE_SERVICE_KEY` → tu base de datos (ver paso 3).
- `ALPHA_VANTAGE_API_KEY` → forex/acciones **intradía real** (gratis en
  alphavantage.co). Sin ella, el forex usa Yahoo Finance (más limitado).
- `NEWSAPI_KEY` → opcional; sin ella las noticias usan RSS público.

> **El archivo `.env.example` es solo una plantilla** que documenta qué
> variables existen, **sin** secretos. El `.env` real con tus claves vive solo
> en tu PC. Así el repositorio nunca contiene credenciales.

### 3. Crear las tablas en Supabase
1. supabase.com → tu proyecto → **SQL Editor → New query**.
2. Pega el contenido de [`db/supabase_schema.sql`](db/supabase_schema.sql) y pulsa **Run**.
3. Copia tu `service_role key` (Project Settings → API) al `.env`.

Si no configuras Supabase, el sistema usa **SQLite local** automáticamente.

### 4. Crear tus TRES claves de administrador 🔐
```powershell
python setup_admin.py
```

### 5. Lanzar (solo accesible desde tu equipo)
```powershell
streamlit run app.py
```
Abre `http://localhost:8501` e introduce tus tres claves.

---

## 🖥️ La terminal

- **Gráfico profesional**: velas + volumen + SMA9/21 + EMA50 + Bandas de Bollinger,
  con crosshair y zoom (estilo TradingView).
- **Panel de señal**: acción 📈/📉/⏸, **medidor de confianza**, Stop Loss y Take
  Profit (por ATR), RSI y sentimiento de noticias.
- **Tiempo real**: la terminal se auto-refresca cada N segundos (configurable)
  usando *fragments* de Streamlit, sin recargar toda la página.
- **Lectura del experto**: explicación concisa de por qué se da la señal.
- **Registrar operación**: botones que guardan tu decisión en la base de datos.
- **Noticias**: titulares recientes del activo con sentimiento coloreado.
- **📡 Radar de mercado**: escanea todos los activos y los ordena por confianza.
- **⏮ Backtesting** y **🤖 Aprendizaje (ML)**.

---

## 🔐 Seguridad

- **Login de triple clave**: tres claves independientes; las tres deben ser
  correctas. Se guardan **hasheadas** (PBKDF2-HMAC-SHA256, 260 000 iteraciones,
  salt por clave), nunca en texto plano. Comparación en tiempo constante y
  **bloqueo temporal** tras varios fallos.
- **Sin secretos en el repo**: `.env`, `.secrets/` y bases de datos locales están
  en `.gitignore`.
- **Solo localhost** por defecto (`.streamlit/config.toml`): el panel no se expone
  a internet salvo que tú lo cambies.
- **Supabase**: la `service_role key` se usa **solo en el servidor**; las tablas
  mantienen RLS activo sin políticas públicas.

> 🔁 Si alguna vez expones una clave (por ejemplo, pegándola en un chat),
> **rótala de inmediato** en Supabase / Alpha Vantage.

---

## 🧠 Motor de decisiones

| Factor | Regla | Peso |
|--------|-------|------|
| RSI | <30 compra / >70 venta | alto |
| Medias (SMA9 vs SMA21) | cruce de tendencia | alto |
| MACD | cruce de señal (momentum) | medio |
| Bollinger | ruptura de banda (volatilidad) | medio |
| Noticias | sentimiento agregado | secundario |
| ATR | Stop Loss / Take Profit | gestión de riesgo |

El motor pondera los factores y produce una acción con **nivel de confianza**.
Señales fuertes (≥65%) disparan alerta visual/sonora y, si lo activas, correo.

---

## 📧 Avisos por correo (opcional, desactivado)
En `.env`: `EMAIL_ENABLED=true` + `SMTP_USER`, `SMTP_PASSWORD` (app password de
Gmail) y `EMAIL_TO`. El sistema enviará un correo cuando aparezca una señal fuerte
(con anti-repetición).
