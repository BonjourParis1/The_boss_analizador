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

-- Seguridad: como usamos la service_role key SOLO en el backend (servidor),
-- mantenemos RLS activado y SIN políticas públicas, de modo que ni la anon key
-- ni el navegador puedan leer/escribir estas tablas directamente.
alter table public.recommendations enable row level security;
alter table public.user_decisions  enable row level security;
