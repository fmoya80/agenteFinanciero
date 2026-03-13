-- Agrega relacion opcional hacia categorias manteniendo columna textual categoria.
alter table public.movimientos
    add column if not exists categoria_id uuid null;

do $$
begin
    if not exists (
        select 1
        from pg_constraint
        where conname = 'movimientos_categoria_id_fkey'
    ) then
        alter table public.movimientos
            add constraint movimientos_categoria_id_fkey
            foreign key (categoria_id)
            references public.categorias(id);
    end if;
end $$;

create index if not exists idx_movimientos_categoria_id on public.movimientos(categoria_id);
