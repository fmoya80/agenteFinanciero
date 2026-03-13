-- Crea categorias por usuario.
create table if not exists public.categorias (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.users(id) on delete cascade,
    nombre text not null,
    descripcion text null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique(user_id, nombre)
);

create index if not exists idx_categorias_user_id on public.categorias(user_id);
