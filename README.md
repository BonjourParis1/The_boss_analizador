# 📊 Guía Experto de Trading

Analista personal y mentor digital de trading **en tiempo real**. Analiza
decenas de mercados (Forex, criptomonedas, acciones, índices y commodities),
calcula indicadores técnicos y te da recomendaciones claras
(**📈 Compra / 📉 Venta / ⏸ Mantener**) que puedes replicar manualmente en
IQ Option u otro bróker.

> ⚠️ **Aviso**: Esta herramienta es educativa y de apoyo a la decisión. No es
> asesoramiento financiero ni garantiza resultados. Operar conlleva riesgo de
> pérdida. Las decisiones son siempre tuyas.

---

## 🗂️ Estructura del proyecto

```
THE_BOSS_ANALIZADOR/
├── app.py                  # Dashboard Streamlit (punto de entrada)
├── config.py               # Configuración y catálogo de mercados
├── setup_admin.py          # Crea/cambia las 3 claves de administrador
├── requirements.txt        # Dependencias
├── .env.example            # Plantilla de variables de entorno
├── .gitignore
│
├── data/                   # Capa de datos (APIs reales + normalización)
│   ├── connectors.py       #   Binance · exchangerate.host · Yahoo Finance · Alpha Vantage
│   └── normalizer.py       #   {timestamp, symbol, price, volume}
│
├── analysis/               # Motor de análisis
│   ├── indicators.py       #   RSI, MACD, SMA/EMA, Bollinger, ATR
│   ├── engine.py           #   Reglas de decisión + gestión de riesgo
│   └── backtest.py         #   Backtesting de la estrategia
│
├── db/                     # Persistencia (SQLAlchemy: SQLite/PostgreSQL)
│   ├── models.py           #   Tablas: recommendations, user_decisions
│   └── database.py         #   Sesiones y operaciones
│
├── ml/                     # Machine Learning
│   └── model.py            #   Aprende de tus decisiones (RandomForest)
│
├── security/               # Seguridad
│   └── auth.py             #   Login de triple clave (PBKDF2 + bloqueo)
│
└── ui/                     # Presentación
    ├── auth_ui.py          #   Pantalla de login
    └── components.py       #   Gráficos Plotly y tarjetas de recomendación
```

---

## 🚀 Puesta en marcha (paso a paso)

### 1. Requisitos
- Python **3.11 o superior**.

### 2. Crear entorno virtual e instalar dependencias

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno (opcional)
```bash
cp .env.example .env      # en Windows:  copy .env.example .env
```
Sin `.env` el sistema funciona con fuentes de datos **sin API key**
(Binance, exchangerate.host, Yahoo Finance). Alpha Vantage es opcional para
forex intradía (rellena `ALPHA_VANTAGE_API_KEY`).

### 4. Crear tus TRES claves de administrador 🔐
```bash
python setup_admin.py
```
Te pedirá las tres claves (no se muestran al escribir) y las guardará
**hasheadas** en `.secrets/admin_keys.json` (ignorado por git).

### 5. Lanzar el dashboard
```bash
streamlit run app.py
```
Se abrirá en `http://localhost:8501`. Introduce tus tres claves para entrar.

---

## 🔐 Seguridad del acceso (triple clave)

- Tres claves **independientes**; las tres deben ser correctas para entrar.
- Se almacenan con **PBKDF2-HMAC-SHA256** (260.000 iteraciones) + *salt*
  aleatorio por clave. Nunca en texto plano.
- Comparación en **tiempo constante** (anti *timing attack*).
- **Bloqueo temporal** tras varios intentos fallidos (anti fuerza bruta;
  configurable con `AUTH_MAX_ATTEMPTS` y `AUTH_LOCKOUT_SECONDS`).
- Cambia las claves cuando quieras volviendo a ejecutar `python setup_admin.py`.

---

## 🧠 Cómo funciona el motor de decisiones

| Indicador | Regla | Señal |
|-----------|-------|-------|
| RSI | < 30 sobreventa / > 70 sobrecompra | 📈 / 📉 |
| Medias móviles (SMA9 vs SMA21) | cruce alcista/bajista | cambio de tendencia |
| MACD | cruce de su línea de señal | momentum |
| Bandas de Bollinger | ruptura de banda | volatilidad/breakout |
| ATR | distancia para Stop Loss / Take Profit | gestión de riesgo |

El motor pondera los votos y produce una acción con **nivel de confianza**.
Las señales fuertes (confianza ≥ 65%) disparan **alerta visual y sonora**.

---

## 🗃️ Base de datos
- **SQLite** por defecto (`db/trading.db`), ideal para prototipo.
- **PostgreSQL** para producción: solo cambia `DATABASE_URL` en `.env`,
  sin tocar el código.

---

## 🤖 Machine Learning
Cada decisión que registras guarda el contexto técnico. Con suficientes
ejemplos, el módulo `ml/model.py` entrena un clasificador que predice qué
harías **tú** ante un estado de mercado, afinando las recomendaciones.

---

## ▶️ Backtesting
La pestaña *Backtesting* aplica las mismas reglas a los datos históricos
cargados y muestra nº de operaciones, tasa de acierto, retorno y curva de
equity.
