-- =============================================================================
-- Cálculo de puntos
-- =============================================================================
--
-- Reglas (los valores salen de `temporadas`; entre paréntesis, los de 2026):
--
--   Top 10, por cada puesto de la boleta:
--     clavado ............................ pts_exacto     (10)
--     errado por un puesto ............... pts_a_uno      (5)
--     entró al top 10 en otro puesto ..... pts_en_top10   (1)
--     terminó fuera del top 10 ........... 0
--       Un piloto puesto P10 que termina P11 cobra 0: el top 10 es el corte.
--
--   Vuelta rápida: acertada = pts_vuelta_rapida (10).
--
--   Piloto seguido (Colapinto en 2026), en cualquier puesto:
--     clavado = pts_seguido_exacto (10), a uno = pts_seguido_a_uno (5).
--     Si abandona, nadie cobra.

create function calcular_puntajes(p_carrera int) returns void
language plpgsql as $$
declare
    t                  temporadas;
    v_vuelta_real      int;
    v_seguido_real     smallint;
begin
    select tp.* into t
      from temporadas tp join carreras c on c.temporada = tp.anio
     where c.id = p_carrera;

    delete from puntajes where carrera_id = p_carrera;

    select vuelta_rapida_id into v_vuelta_real
      from resultados where carrera_id = p_carrera;
    if not found then
        return;                          -- sin resultado no hay puntos
    end if;

    -- Top 10 ------------------------------------------------------------------
    insert into puntajes (carrera_id, participante_id, rubro, slot, piloto_id,
                          posicion_predicha, posicion_real, tipo, puntos)
    select carrera_id, participante_id, 'top10', slot, piloto_id,
           slot, posicion_real, tipo,
           case tipo when 'exacto'   then t.pts_exacto
                     when 'a_uno'    then t.pts_a_uno
                     when 'en_top10' then t.pts_en_top10
                     else 0 end
      from (
        select v.carrera_id, v.participante_id, s.slot::smallint as slot,
               s.piloto_id, rp.posicion as posicion_real,
               case when rp.posicion is null or rp.posicion > 10 then 'fuera'
                    when rp.posicion = s.slot                     then 'exacto'
                    when abs(rp.posicion - s.slot) = 1            then 'a_uno'
                    else 'en_top10'
               end::tipo_acierto as tipo
          from votos v
         cross join lateral unnest(v.top10) with ordinality as s(piloto_id, slot)
          left join resultados_pilotos rp
                 on rp.carrera_id = v.carrera_id and rp.piloto_id = s.piloto_id
         where v.carrera_id = p_carrera
           and s.piloto_id is not null
      ) x;

    -- Vuelta rápida -----------------------------------------------------------
    insert into puntajes (carrera_id, participante_id, rubro, slot, piloto_id,
                          tipo, puntos)
    select v.carrera_id, v.participante_id, 'vuelta_rapida', 0, v.vuelta_rapida_id,
           x.tipo,
           case when x.tipo = 'exacto' then t.pts_vuelta_rapida else 0 end
      from votos v
     cross join lateral (select
           case when v_vuelta_real is null           then 'sin_dato'
                when v.vuelta_rapida_id is null      then 'sin_prediccion'
                when v.vuelta_rapida_id = v_vuelta_real then 'exacto'
                else 'errado'
           end::tipo_acierto as tipo) x
     where v.carrera_id = p_carrera;

    -- Piloto seguido ----------------------------------------------------------
    if t.piloto_seguido_id is not null then
        select posicion into v_seguido_real
          from resultados_pilotos
         where carrera_id = p_carrera and piloto_id = t.piloto_seguido_id;

        insert into puntajes (carrera_id, participante_id, rubro, slot, piloto_id,
                              posicion_predicha, posicion_real, tipo, puntos)
        select v.carrera_id, v.participante_id, 'piloto_seguido', 0,
               t.piloto_seguido_id, v.pos_seguido, v_seguido_real, x.tipo,
               case x.tipo when 'exacto' then t.pts_seguido_exacto
                           when 'a_uno'  then t.pts_seguido_a_uno
                           else 0 end
          from votos v
         cross join lateral (select
               case when v.pos_seguido is null                    then 'sin_prediccion'
                    when v_seguido_real is null                   then 'no_termino'
                    when v.pos_seguido = v_seguido_real           then 'exacto'
                    when abs(v.pos_seguido - v_seguido_real) = 1  then 'a_uno'
                    else 'errado'
               end::tipo_acierto as tipo) x
         where v.carrera_id = p_carrera;
    end if;
end;
$$;

-- =============================================================================
-- Vistas para la página
-- =============================================================================

create view puntos_por_carrera with (security_invoker = true) as
select p.carrera_id, c.temporada, c.ronda, c.nombre as carrera,
       p.participante_id, pa.apodo, sum(p.puntos)::int as puntos,
       count(*) filter (where p.rubro = 'top10' and p.tipo = 'exacto')::int as exactos
  from puntajes p
  join carreras c       on c.id = p.carrera_id
  join participantes pa on pa.id = p.participante_id
 group by p.carrera_id, c.temporada, c.ronda, c.nombre, p.participante_id, pa.apodo;

create view ranking with (security_invoker = true) as
select temporada, participante_id, apodo,
       sum(puntos)::int                 as puntos,
       count(*)::int                    as carreras_jugadas,
       sum(exactos)::int                as exactos,
       rank() over (partition by temporada order by sum(puntos) desc)::int as posicion
  from puntos_por_carrera
 group by temporada, participante_id, apodo;
