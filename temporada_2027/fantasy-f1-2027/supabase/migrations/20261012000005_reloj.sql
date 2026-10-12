-- =============================================================================
-- El reloj
-- =============================================================================
--
-- En 2026 el reloj era el cron de GitHub Actions: atrasaba entre 1 h 40 y
-- 5 h 24 y a veces no corría. Acá el reloj es pg_cron, que corre dentro de la
-- propia base, al minuto.
--
-- Solo existe en Supabase. En la base local de los tests no está, y este
-- archivo no hace nada.

do $$
begin
    if not exists (select 1 from pg_available_extensions where name = 'pg_cron') then
        raise notice 'pg_cron no disponible: no se programa el reloj';
        return;
    end if;

    create extension if not exists pg_cron;

    -- Cada 5 minutos: abrir y cerrar votaciones, recordatorios, resultados
    -- definitivos.
    perform cron.schedule('avanzar-estados', '*/5 * * * *',
                          'select public.avanzar_estados()');
end;
$$;
