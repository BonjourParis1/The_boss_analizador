-- ============================================================
--  Guía Experto de Trading — Esquema para Supabase (PostgreSQL)
--
--  CÓMO USARLO:
--    1) Entra a tu proyecto en https://supabase.com
--    2) Menú lateral -> SQL Editor -> New query
--    3) Pega TODO este archivo y pulsa "Run".
--  Esto crea las tablas que usa el sistema. Solo hay que hacerlo una vez.
-- ============================================================

-- Recomendaciones generadas por el motor de análisis
create table if not exists public.recommendations (
    id           bigint generated always as identity primary key,
    created_at   timestamptz not null default now(),
    symbol       text        not null,
    action       text        not null,             -- COMPRA / VENTA / MANTENER
    confidence   double precision not null,
    price        double precision not null,
    rsi          double precision,
    atr          double precision,
    stop_loss    double precision,
    take_profit  double precision,
    news_score   double precision,                 -- sentimiento de noticias (-1..1)
    reasons      jsonb
);
create index if not exists idx_reco_symbol_time
    on public.recommendations (symbol, created_at desc);

-- Decisiones que TÚ tomas frente a cada recomendación
create table if not exists public.user_decisions (
    id                 bigint generated always as identity primary key,
    created_at         timestamptz not null default now(),
    recommendation_id  bigint references public.recommendations (id) on delete set null,
    symbol             text        not null,
    user_action        text        not null,        -- lo que hiciste
    bot_action         text        not null,        -- lo que sugirió el bot
    price_at_decision  double precision not null,
    note               text,
    outcome            text default 'pendiente'      -- acierto / fallo / pendiente
);
create index if not exists idx_dec_time
    on public.user_decisions (created_at desc);

-- CONOCIMIENTO que le enseñas al cerebro (texto/YouTube analizado, auto-investigación).
-- Esto es "lo que aprende": queda guardado en la NUBE y el cerebro lo reutiliza.
create table if not exists public.knowledge (
    id          bigint generated always as identity primary key,
    created_at  timestamptz not null default now(),
    kind        text        not null,                 -- texto / youtube / auto
    source      text,                                 -- url o etiqueta de origen
    sentiment   double precision default 0,           -- sesgo aprendido (-1..1)
    summary     text,                                 -- resumen/insight para el cerebro
    content     text                                  -- contenido bruto (recortado)
);
create index if not exists idx_knowledge_time
    on public.knowledge (created_at desc);

-- SEÑALES y su RESULTADO (acierto/fallo) para medir la precisión del sistema.
create table if not exists public.signals (
    id              bigint generated always as identity primary key,
    created_at      timestamptz not null default now(),
    entry_ts        double precision not null,         -- epoch de entrada (para vencimiento)
    symbol          text        not null,
    direction       text        not null,              -- SUBE / BAJA
    expiry_seconds  integer     not null,              -- duración de la inversión
    entry_price     double precision not null,
    exit_price      double precision,
    status          text default 'pending',            -- pending / win / loss
    source          text default 'auto'                -- auto / terminal / manual
);
create index if not exists idx_signals_symbol_status
    on public.signals (symbol, status);
-- Foto de indicadores en la entrada (para que el modelo aprenda de resultados reales)
alter table public.signals add column if not exists features jsonb;

-- REGISTRO DE ACCESOS: cada intento de inicio de sesión (correcto/fallido) y cierre.
create table if not exists public.access_log (
    id          bigint generated always as identity primary key,
    created_at  timestamptz not null default now(),
    ts          double precision,                    -- epoch del evento
    event       text        not null,                -- ok / fallo / logout
    detail      text
);
create index if not exists idx_access_ts on public.access_log (ts desc);

-- AJUSTES del usuario (capital disponible, riesgo por operación, pago, etc.).
create table if not exists public.app_settings (
    key         text primary key,
    value       jsonb,
    updated_at  timestamptz not null default now()
);

-- Seguridad: como usamos la service_role key SOLO en el backend (servidor),
-- mantenemos RLS activado y SIN políticas públicas, de modo que ni la anon key
-- ni el navegador puedan leer/escribir estas tablas directamente.
alter table public.recommendations enable row level security;
alter table public.user_decisions  enable row level security;
alter table public.knowledge        enable row level security;
alter table public.signals          enable row level security;
alter table public.access_log       enable row level security;
alter table public.app_settings     enable row level security;
