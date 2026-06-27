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
- **Lectura de velas**: detecta patrones (martillo, envolvente, doji, estrella
  del amanecer/atardecer…), tendencia y soportes/resistencias, como un trader.
- **Tiempo real**: las **criptomonedas** se transmiten en vivo — la última vela se
  mueve tick a tick (Binance) y hay un modo **"Línea en vivo"** que dibuja el precio
  por segundos como IQ Option. **Forex/acciones** usan APIs gratuitas limitadas
  (Alpha Vantage ~25 llamadas/día), por lo que se actualizan de forma manual.
- **Temporalidades y zoom**: selector de 1m a 1M y botones de zoom temporal
  (15m/1H/4H/1D/1S/Todo) + scroll/arrastre sobre el gráfico, como en TradingView.
- **Velas por segundos**: tipos de gráfico **"Velas 5s"** y **"Velas 30s"** que se
  construyen en vivo desde los ticks — ves el mercado fluctuar por segundos.
- **Panel lateral**: filtro por categoría (Cripto/Forex/Acciones/Índices/Materias),
  32 activos, y conmutadores de indicadores (medias, Bollinger, volumen, RSI/MACD).
- **🎯 Plan autónomo**: en cada refresco el sistema decide y muestra qué hacer —
  **COMPRA (CALL) / VENTA (PUT) / ESPERAR** con **duración sugerida** (30s/1m/3m/5m)
  según volatilidad y señal, combinando el motor técnico con el autoaprendizaje.
  Acumula un feed de **operaciones sugeridas** en el tiempo.
- **Alertas en paralelo**: mientras observas, el sistema detecta patrones y acumula
  un feed de **🔔 alertas en vivo** de señales fuertes. Para vigilancia 24/7 de TODOS
  los activos a la vez, usa el escáner (`scanner.py`).
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

---

## 🧠 Cerebro IA (GRATIS, sin API de pago) — opcional
La pestaña **Cerebro IA** puede **razonar la operación** del activo en lenguaje
natural (lectura, escenario probable y gestión de riesgo, siempre en probabilidades) y
**procesar contenido que le adjuntes**: pegas texto o una **URL de YouTube** (analiza
la *transcripción*) y extrae resumen, sesgo, ideas accionables y banderas rojas.
Elige proveedor en `.env` con `LLM_PROVIDER` (todas opciones gratuitas):
- **`gemini`** — la más fácil (nube, sin instalar nada). Clave gratis en
  aistudio.google.com/apikey → `GEMINI_API_KEY`.
- **`ollama`** — 100% local y privado (instala ollama.com → `ollama pull llama3.1`).
- **`openai_compatible`** — cualquier servidor estilo OpenAI: LM Studio (local) o free
  tiers en la nube como **Groq / Together / DeepInfra / Hugging Face** (pon su
  `OPENAI_BASE_URL`, `OPENAI_API_KEY` y `LLM_MODEL`).

### 📡 Datos en tiempo real adicionales (opcional)
Con `FINNHUB_API_KEY` (gratis, 60/min en finnhub.io) las **acciones de EE. UU.**
también muestran **precio en vivo tick a tick** en el encabezado y la línea en vivo.

## 🤖 Aprendizaje (apoyo probabilístico, no predice el futuro)
- **Autoaprendizaje del histórico** (`analysis/auto_learn.py`): aprende solo, sin
  que operes — etiqueta cada vela por lo que pasó después y entrena un modelo para
  anticipar SUBE/LATERAL/BAJA, mostrando su **precisión validada**.
- **Aprendizaje de tus decisiones** (`ml/model.py`): aprende qué harías **tú** según
  los indicadores, a partir de las decisiones que registras.

## 🛰️ Escáner autónomo 24/7
`scanner.py` es un proceso independiente que escanea **todos** los activos cada N
minutos (`SCAN_INTERVAL_MINUTES`), guarda recomendaciones y, si activas el correo,
avisa de señales fuertes aunque no tengas el navegador abierto:
```powershell
python scanner.py            # bucle continuo
python scanner.py --once     # una sola pasada (para cron/pruebas)
```
