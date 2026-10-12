-- =============================================================================
-- Quién puede ver y tocar qué
-- =============================================================================
--
-- La página habla directo con la base usando la clave pública de Supabase.
-- Esa clave la puede ver cualquiera, así que la seguridad no puede depender
-- de la página: vive acá.
--
--   - Leer: el calendario, los pilotos, los resultados y los puntos son
--     públicos. Los votos ajenos se ven recién cuando larga la carrera
--     (antes no, para que nadie copie).
--   - Escribir: nadie escribe ninguna tabla directamente. Votar se hace solo
--     con votar(); cargar resultados y avanzar estados, solo el sistema.

alter table temporadas            enable row level security;
alter table pilotos               enable row level security;
alter table participantes         enable row level security;
alter table carreras              enable row level security;
alter table votos                 enable row level security;
alter table votos_auditoria       enable row level security;
alter table resultados            enable row level security;
alter table resultados_pilotos    enable row level security;
alter table resultados_historial  enable row level security;
alter table puntajes              enable row level security;
alter table eventos               enable row level security;

-- Supabase da por defecto todos los permisos sobre las tablas nuevas a los
-- roles de la página. Se sacan todos y se devuelve solo lo necesario.
revoke all on all tables    in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke all on all functions in schema public from public, anon, authenticated;

-- Lectura pública ------------------------------------------------------------

grant select on temporadas, pilotos, carreras, resultados, resultados_pilotos,
                puntajes, puntos_por_carrera, ranking
   to anon, authenticated;

create policy lectura_publica on temporadas         for select using (true);
create policy lectura_publica on pilotos            for select using (true);
create policy lectura_publica on carreras           for select using (true);
create policy lectura_publica on resultados         for select using (true);
create policy lectura_publica on resultados_pilotos for select using (true);
create policy lectura_publica on puntajes           for select using (true);

-- De los participantes se ve el apodo, nunca a qué usuario corresponden.
grant select (id, apodo, activo) on participantes to anon, authenticated;
create policy lectura_publica on participantes for select using (true);

-- Votos: el propio siempre; los ajenos, desde la largada.
grant select on votos to anon, authenticated;
create policy ver_votos on votos for select using (
    participante_id = participante_actual()
    or exists (select 1 from carreras c
                where c.id = votos.carrera_id and now() >= c.largada)
);

-- Funciones que puede llamar la página --------------------------------------

grant execute on function votar(int, int[], int, smallint) to authenticated;
grant execute on function participante_actual()            to anon, authenticated;
grant execute on function pendientes_de_votar(int)          to anon, authenticated;

-- calcular_puntajes, registrar_resultado y avanzar_estados quedan solo para
-- el dueño de la base y para las funciones del servidor (service_role).
