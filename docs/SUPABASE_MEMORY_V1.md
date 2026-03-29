# Supabase Memory V1 (Memoria Critica)

## Alcance fase 1
- clientes
- cliente_perfiles
- cliente_areas
- cliente_workflow
- cliente_workpapers
- cliente_hallazgos

## SQL base sugerido
```sql
create table if not exists clientes (
  cliente_id text primary key,
  nombre text not null,
  sector text,
  schema_version text not null default 'v1',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists cliente_perfiles (
  cliente_id text primary key references clientes(cliente_id) on delete cascade,
  perfil_json jsonb not null,
  schema_version text not null default 'v1',
  updated_at timestamptz not null default now()
);

create table if not exists cliente_areas (
  cliente_id text not null references clientes(cliente_id) on delete cascade,
  area_code text not null,
  area_json jsonb not null,
  schema_version text not null default 'v1',
  updated_at timestamptz not null default now(),
  primary key (cliente_id, area_code)
);

create table if not exists cliente_workflow (
  cliente_id text primary key references clientes(cliente_id) on delete cascade,
  workflow_json jsonb not null,
  schema_version text not null default 'v1',
  updated_at timestamptz not null default now()
);

create table if not exists cliente_workpapers (
  cliente_id text primary key references clientes(cliente_id) on delete cascade,
  workpapers_json jsonb not null,
  schema_version text not null default 'v1',
  updated_at timestamptz not null default now()
);

create table if not exists cliente_hallazgos (
  cliente_id text primary key references clientes(cliente_id) on delete cascade,
  hallazgos_json jsonb not null,
  schema_version text not null default 'v1',
  updated_at timestamptz not null default now()
);
```

## RLS minimo recomendado
```sql
create table if not exists user_clientes (
  user_id text not null,
  cliente_id text not null references clientes(cliente_id) on delete cascade,
  primary key (user_id, cliente_id)
);
```

Aplicar RLS en todas las tablas de memoria:
- permitir `select/insert/update/delete` solo cuando exista relacion en `user_clientes`.
- para procesos de backend server-to-server usar service role key.

## Variables backend
- `USE_SUPABASE_MEMORY=true`
- `SUPABASE_URL=https://<project>.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY=<service_role_key>`
- `SUPABASE_TIMEOUT_SECONDS=8`

## Backfill
```bash
python -m backend.scripts.supabase_memory_backfill
python -m backend.scripts.supabase_memory_backfill --cliente bf_holding_2025
```
