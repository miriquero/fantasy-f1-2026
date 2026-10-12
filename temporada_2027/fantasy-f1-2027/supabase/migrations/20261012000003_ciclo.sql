-- =============================================================================
-- Votación, resultados y ciclo de vida de cada carrera
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Quién está votando
-- -----------------------------------------------------------------------------
--
-- Todo el resto del sistema pregunta "quién sos" solo a través de esta
-- función. Cómo se identifica cada uno (link por mail, link personal, Google)
-- todavía está en discusión: el día que se decida, se cambia esta función y
-- nada más.

create function participante_actual() returns uuid
language sql stable security definer set search_path = public as $$
    select id from participantes where user_id = auth.uid() and activo
$$;

-- -----------------------------------------------------------------------------
-- Votar
-- -----------------------------------------------------------------------------
--
-- Única puerta de entrada de los votos. El corte es la hora de largada,
-- medida con el reloj de la base: no depende de que ningún script corra a
-- tiempo. Se puede cambiar el voto cuantas veces se quiera hasta la largada.

create function votar(
    p_carrera        int,
    p_top10          int[],
    p_vuelta_rapida  int,
    p_pos_seguido    smallint default null
) returns votos
language plpgsql security definer set search_path = public as $$
declare
    v_participante  uuid := participante_actual();
    c               carreras;
    t               temporadas;
    v_cant_pilotos  int;
    v_voto          votos;
begin
    if v_participante is null then
        raise exception 'Tenés que entrar con tu usuario para votar'
            using errcode = '28000';
    end if;

    select * into c from carreras where id = p_carrera;
    if not found then
        raise exception 'Esa carrera no existe' using errcode = 'P0002';
    end if;
    if c.estado <> 'abierta' or now() >= c.largada then
        raise exception 'La votación de % está cerrada', c.nombre
            using errcode = 'P0001';
    end if;

    select * into t from temporadas where anio = c.temporada;
    select count(*) into v_cant_pilotos from pilotos where temporada = c.temporada;

    if p_top10 is null or cardinality(p_top10) <> 10
       or array_position(p_top10, null) is not null then
        raise exception 'Completá los diez puestos' using errcode = '22023';
    end if;
    if (select count(distinct x) from unnest(p_top10) x) <> 10 then
        raise exception 'Pusiste el mismo piloto en dos puestos' using errcode = '22023';
    end if;
    if exists (select 1 from unnest(p_top10) x
                where not exists (select 1 from pilotos
                                   where id = x and temporada = c.temporada)) then
        raise exception 'Hay un piloto que no corre esta temporada' using errcode = '22023';
    end if;
    if p_vuelta_rapida is null
       or not exists (select 1 from pilotos
                       where id = p_vuelta_rapida and temporada = c.temporada) then
        raise exception 'Elegí quién hace la vuelta rápida' using errcode = '22023';
    end if;
    if t.piloto_seguido_id is not null
       and (p_pos_seguido is null or p_pos_seguido not between 1 and v_cant_pilotos) then
        raise exception 'Elegí el puesto del piloto seguido (entre 1 y %)', v_cant_pilotos
            using errcode = '22023';
    end if;

    insert into votos (participante_id, carrera_id, top10, vuelta_rapida_id, pos_seguido)
    values (v_participante, p_carrera, p_top10, p_vuelta_rapida,
            case when t.piloto_seguido_id is null then null else p_pos_seguido end)
    on conflict (participante_id, carrera_id) do update
       set top10            = excluded.top10,
           vuelta_rapida_id = excluded.vuelta_rapida_id,
           pos_seguido      = excluded.pos_seguido,
           actualizado      = now()
    returning * into v_voto;

    return v_voto;
end;
$$;

-- -----------------------------------------------------------------------------
-- Auditoría de votos
-- -----------------------------------------------------------------------------
--
-- Corre para cualquier escritura, venga de votar() o de un admin editando la
-- tabla a mano. Si el cambio es posterior a la largada, además deja un evento
-- para que se avise: es lo que en 2026 pasó sin que nadie lo viera.

create function auditar_voto() returns trigger
language plpgsql security definer set search_path = public as $$
declare
    v_fila      votos := coalesce(new, old);
    v_tarde     boolean;
    v_operacion text := case tg_op when 'INSERT' then 'alta'
                                   when 'UPDATE' then 'cambio'
                                   else 'baja' end;
begin
    select coalesce(now() >= largada, false) into v_tarde
      from carreras where id = v_fila.carrera_id;

    insert into votos_auditoria (voto_id, participante_id, carrera_id, operacion,
                                 antes, despues, despues_de_largada, quien)
    values (v_fila.id, v_fila.participante_id, v_fila.carrera_id, v_operacion,
            case when tg_op <> 'INSERT' then to_jsonb(old) end,
            case when tg_op <> 'DELETE' then to_jsonb(new) end,
            v_tarde, auth.uid());

    if v_tarde then
        insert into eventos (tipo, carrera_id, datos)
        values ('voto_fuera_de_termino', v_fila.carrera_id,
                jsonb_build_object(
                    'apodo', (select apodo from participantes where id = v_fila.participante_id),
                    'operacion', v_operacion));
    end if;

    return null;
end;
$$;

create trigger votos_auditoria
after insert or update or delete on votos
for each row execute function auditar_voto();

-- -----------------------------------------------------------------------------
-- Resultados
-- -----------------------------------------------------------------------------

-- Foto comparable de un resultado: {"clasificacion": {codigo: posicion},
-- "vuelta_rapida": codigo}. Sirve para saber si la API trajo algo distinto.
create function foto_resultado(p_carrera int) returns jsonb
language sql stable as $$
    select jsonb_build_object(
        'clasificacion', coalesce((
            select jsonb_object_agg(p.codigo_api, rp.posicion)
              from resultados_pilotos rp join pilotos p on p.id = rp.piloto_id
             where rp.carrera_id = p_carrera), '{}'::jsonb),
        'vuelta_rapida', (
            select p.codigo_api
              from resultados r join pilotos p on p.id = r.vuelta_rapida_id
             where r.carrera_id = p_carrera))
$$;

-- Carga (o corrige) el resultado de una carrera y recalcula los puntos, todo
-- en una transacción.
--
-- p_clasificacion: [{"piloto": "max_verstappen", "nombre": "Max Verstappen",
--                    "numero": 1, "equipo": "Red Bull", "posicion": 1}, ...]
--   posicion null = no terminó.
-- p_vuelta_rapida: codigo_api del piloto, o null si la API no lo informa.
--
-- Si aparece un piloto que no estaba (un reemplazo a mitad de año), se agrega
-- solo. En 2026 eso obligaba a editar la lista a mano.
--
-- Devuelve 'nuevo', 'corregido' o 'sin_cambios'.
create function registrar_resultado(
    p_carrera        int,
    p_clasificacion  jsonb,
    p_vuelta_rapida  text,
    p_fuente         text
) returns text
language plpgsql security definer set search_path = public as $$
declare
    c          carreras;
    v_antes    jsonb;
    v_despues  jsonb;
    v_hay      boolean;
    v_estado   text;
begin
    select * into c from carreras where id = p_carrera for update;
    if not found then
        raise exception 'La carrera % no existe', p_carrera;
    end if;
    if c.estado = 'cancelada' then
        raise exception '% está cancelada', c.nombre;
    end if;
    if now() < c.largada then
        raise exception '% todavía no largó', c.nombre;
    end if;

    insert into pilotos (temporada, codigo_api, nombre, numero, equipo)
    select c.temporada, e->>'piloto', coalesce(e->>'nombre', e->>'piloto'),
           (e->>'numero')::smallint, e->>'equipo'
      from jsonb_array_elements(p_clasificacion) e
    on conflict (temporada, codigo_api) do nothing;

    v_hay := exists (select 1 from resultados where carrera_id = p_carrera);
    v_antes := foto_resultado(p_carrera);

    v_despues := jsonb_build_object(
        'clasificacion', coalesce((
            select jsonb_object_agg(e->>'piloto', (e->>'posicion')::int)
              from jsonb_array_elements(p_clasificacion) e), '{}'::jsonb),
        'vuelta_rapida', p_vuelta_rapida);

    if v_hay and v_antes = v_despues then
        return 'sin_cambios';
    end if;

    if v_hay then
        insert into resultados_historial (carrera_id, anterior, nuevo, fuente)
        values (p_carrera, v_antes, v_despues, p_fuente);
        delete from resultados_pilotos where carrera_id = p_carrera;
    end if;

    insert into resultados (carrera_id, vuelta_rapida_id, fuente, actualizado)
    values (p_carrera,
            (select id from pilotos where temporada = c.temporada and codigo_api = p_vuelta_rapida),
            p_fuente, now())
    on conflict (carrera_id) do update
       set vuelta_rapida_id = excluded.vuelta_rapida_id,
           fuente           = excluded.fuente,
           actualizado      = now();

    insert into resultados_pilotos (carrera_id, piloto_id, posicion)
    select p_carrera, p.id, (e->>'posicion')::smallint
      from jsonb_array_elements(p_clasificacion) e
      join pilotos p on p.temporada = c.temporada and p.codigo_api = e->>'piloto';

    perform calcular_puntajes(p_carrera);

    update carreras set estado = 'provisoria' where id = p_carrera;

    v_estado := case when v_hay then 'corregido' else 'nuevo' end;
    insert into eventos (tipo, carrera_id, datos)
    values (case when v_hay then 'resultado_corregido' else 'resultado' end,
            p_carrera,
            case when v_hay then jsonb_build_object('anterior', v_antes, 'nuevo', v_despues)
                 else '{}'::jsonb end);

    return v_estado;
end;
$$;

-- -----------------------------------------------------------------------------
-- Ciclo de vida
-- -----------------------------------------------------------------------------

-- Quiénes todavía no votaron una carrera.
create function pendientes_de_votar(p_carrera int) returns setof text
language sql stable security definer set search_path = public as $$
    select pa.apodo from participantes pa
     where pa.activo
       and not exists (select 1 from votos v
                        where v.carrera_id = p_carrera and v.participante_id = pa.id)
     order by pa.apodo
$$;

-- Hace avanzar todas las carreras según el reloj. Pensada para correr cada
-- pocos minutos (pg_cron). Es idempotente: correrla dos veces seguidas no
-- hace nada la segunda vez, y si una corrida se pierde, la siguiente pone
-- todo al día.
create function avanzar_estados() returns int
language plpgsql security definer set search_path = public as $$
declare
    v_cambios int := 0;
    v_n       int;
    rec       record;
begin
    -- Cerrar: llegó la largada. Primero, para que una carrera cuya apertura y
    -- largada ya pasaron no se "abra" de mentira.
    with cerradas as (
        update carreras set estado = 'cerrada'
         where estado in ('programada', 'abierta') and now() >= largada
        returning id, nombre)
    insert into eventos (tipo, carrera_id, datos)
    select 'votacion_cerrada', id,
           jsonb_build_object('carrera', nombre,
                              'no_votaron', to_jsonb(array(select pendientes_de_votar(id))))
      from cerradas;
    get diagnostics v_n = row_count;
    v_cambios := v_cambios + v_n;

    -- Abrir: faltan menos de `dias_apertura` días.
    with abiertas as (
        update carreras c set estado = 'abierta'
          from temporadas t
         where t.anio = c.temporada
           and c.estado = 'programada'
           and now() >= c.largada - make_interval(days => t.dias_apertura)
        returning c.id, c.nombre, c.largada)
    insert into eventos (tipo, carrera_id, datos)
    select 'votacion_abierta', id,
           jsonb_build_object('carrera', nombre, 'largada', largada)
      from abiertas;
    get diagnostics v_n = row_count;
    v_cambios := v_cambios + v_n;

    -- Recordatorios: 24 h y 1 h antes, solo si falta alguien. Uno de cada
    -- tipo por carrera: la existencia del evento es la marca de "ya avisado".
    for rec in
        select c.id, c.nombre, c.largada, x.tipo
          from carreras c
         cross join (values ('recordatorio_24h', interval '24 hours'),
                            ('recordatorio_1h',  interval '1 hour')) x(tipo, antes)
         where c.estado = 'abierta'
           and now() >= c.largada - x.antes
           and not exists (select 1 from eventos e
                            where e.carrera_id = c.id and e.tipo = x.tipo)
    loop
        if exists (select pendientes_de_votar(rec.id)) then
            insert into eventos (tipo, carrera_id, datos)
            values (rec.tipo, rec.id,
                    jsonb_build_object('carrera', rec.nombre, 'largada', rec.largada,
                                       'no_votaron', to_jsonb(array(select pendientes_de_votar(rec.id)))));
            v_cambios := v_cambios + 1;
        end if;
    end loop;

    -- Definitivo: el resultado no cambió en `horas_para_final` horas.
    with finales as (
        update carreras c set estado = 'final'
          from resultados r, temporadas t
         where r.carrera_id = c.id and t.anio = c.temporada
           and c.estado = 'provisoria'
           and now() >= r.actualizado + make_interval(hours => t.horas_para_final)
        returning c.id, c.nombre)
    insert into eventos (tipo, carrera_id, datos)
    select 'resultado_final', id, jsonb_build_object('carrera', nombre)
      from finales;
    get diagnostics v_n = row_count;
    v_cambios := v_cambios + v_n;

    return v_cambios;
end;
$$;
