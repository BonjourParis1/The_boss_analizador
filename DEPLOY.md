# Despliegue en la nube

Arquitectura recomendada:
- **GitHub** → guarda el **código** (este repo).
- **Supabase** → guarda los **datos** (recomendaciones, decisiones, conocimiento, señales).
- **Streamlit Community Cloud** → **ejecuta** la app (gratis, conecta con GitHub).

> ⚠️ **Vercel no sirve** para esta app: Streamlit necesita un servidor siempre en
> marcha y Vercel es *serverless* (se apaga entre peticiones). Usa una de las
> opciones de abajo.

---

## 1) Preparar Supabase (datos en la nube, no en tu PC)
1. Entra a tu proyecto en https://supabase.com → **SQL Editor → New query**.
2. Pega **todo** el archivo [`db/supabase_schema.sql`](db/supabase_schema.sql) y pulsa **Run**.
   - Crea las tablas: `recommendations`, `user_decisions`, `knowledge`, `signals`.
3. Listo: el conocimiento que enseñes y la precisión se guardarán en Supabase.

## 2) Generar los secretos
En tu PC:
```bash
python setup_admin.py        # define tus 3 claves (si aún no lo hiciste)
python cloud_secrets.py      # imprime SESSION_SECRET y ADMIN_KEYS_JSON para copiar
```

## 3) Desplegar en Streamlit Community Cloud
1. Ve a https://share.streamlit.io → **New app** → elige este repo de GitHub.
2. **Main file path:** `app.py`.
3. En **Advanced settings → Secrets**, pega (formato TOML):
   ```toml
   SESSION_SECRET = "....(de cloud_secrets.py)...."
   ADMIN_KEYS_JSON = '{"hashes":["..."],"version":1}'

   SUPABASE_URL = "https://TU-PROYECTO.supabase.co"
   SUPABASE_SERVICE_KEY = "eyJ..."
   GEMINI_API_KEY = "AQ..."
   DEEPSEEK_API_KEY = "sk-..."
   FINNHUB_API_KEY = "..."
   TWELVEDATA_API_KEY = "..."
   YOUTUBE_API_KEY = "..."
   ALPHA_VANTAGE_API_KEY = "..."
   SCAN_INTERVAL_MINUTES = "2"
   ```
4. **Deploy.** La app quedará en una URL pública protegida por tu triple clave.

> Streamlit Cloud expone los *secrets* también como variables de entorno, por eso
> la app (que lee `os.getenv`) los toma sin cambios.

---

## Motor autónomo 24/7 (que aprenda aunque no tengas la página abierta)

El dashboard en Streamlit Cloud **se duerme** con inactividad, así que el motor solo
corre mientras la página está abierta. Para que analice y APRENDA de forma continua,
ejecuta el motor por separado. Todo se guarda en Supabase; el dashboard lo lee.

### Opción A — GitHub Actions (GRATIS si el repo es público) ⭐
Ya incluido en `.github/workflows/autonomous.yml`: lanza `worker_once.py` cada 15 min.
1. GitHub → tu repo → **Settings → Secrets and variables → Actions → New repository secret**
   y crea: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`,
   `FINNHUB_API_KEY`, `TWELVEDATA_API_KEY`, `ALPHA_VANTAGE_API_KEY`.
2. Pestaña **Actions** → habilítalas si te lo pide → puedes lanzar "Run workflow" a mano.
- **Repo público:** Actions es **gratis e ilimitado** → ideal.
- **Repo privado:** GitHub da 2000 min/mes gratis; cada pasada tarda ~2 min, así que
  cada 15 min consume el cupo en ~2 semanas. Si es privado, sube el intervalo del cron
  (p. ej. `*/30`) o usa la Opción B.

### Opción B — Worker siempre encendido (Render / Railway / Fly.io)
Para granularidad de minutos sin límite, un proceso permanente con `worker.py`:
- **Render:** incluido `render.yaml` (New + → Blueprint). El worker es de pago (~7 USD/mes);
  pega tus claves cuando te las pida.
- **Railway:** New Project → Deploy from repo → Start command `python worker.py` → añade
  las variables. Cuesta por uso (~5 USD/mes).
- **Fly.io:** tiene una franja gratuita que suele alcanzar para un worker pequeño.

> El dashboard sigue en Streamlit Cloud; el worker solo alimenta Supabase. No necesitas
> ejecutar las dos cosas en el mismo sitio.

## Notas importantes
- **Nunca** subas claves a GitHub. Van solo en *Secrets* del hosting o en tu `.env`
  local (ambos ignorados por git).
- **Motor autónomo 24/7:** en Streamlit Cloud la app se *duerme* con inactividad, así
  que el motor no corre de forma continua. Para 24/7 real usa **Render/Railway**
  (un *worker* aparte) o un **VPS** pequeño.
- Sin Supabase configurado, la app cae a archivos locales de respaldo (solo para
  desarrollo); en la nube **siempre** configura Supabase.
