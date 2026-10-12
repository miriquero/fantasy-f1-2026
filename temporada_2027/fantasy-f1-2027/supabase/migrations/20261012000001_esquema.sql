-- =============================================================================
-- Esquema del torneo
-- =============================================================================
--
-- Principio: lo que describe la realidad (pilotos, carreras, horarios) son
-- datos, no código. Y lo que define el juego (cuánto paga cada acierto, cuál
-- es el piloto que se sigue) también: vive en `temporadas`, así que cambiar
-- una regla para 2027 es editar una fila, no tocar el cálculo.

-- -----------------------------------------------------------------------------
-- Temporadas y reglas
-- -----------------------------------------------------------------------------

create table temporadas (
    anio                smallint primary key,
    -- El "piloto seguido" es la categoría que en 2026 fue Colapinto. Si en
    -- 2027 cambia o desaparece, se cambia acá; null = la categoría no existe.
    piloto_seguido_id   int,
    -- Cuántos días antes de la largada se abre la votación.
    dias_apertura       smallint not null default 6 check (dias_apertura > 0),
    -- Cuántas horas sin cambios en el resultado para darlo por definitivo.
    horas_para_final    smallint not null default 48 check (horas_para_final > 0),
    -- Puntaje. Los valores por defecto son las reglas de 2026.
    pts_exacto          smallint not null default 10,
    pts_a_uno           smallint not null default 5,
    pts_en_top10        smallint not null default 1,
    pts_vuelta_rapida   smallint not null default 10,
    pts_seguido_exacto  smallint not null default 10,
    pts_seguido_a_uno   smallint not null default 5
);

-- -----------------------------------------------------------------------------
-- Pilotos
-- -----------------------------------------------------------------------------
--
-- Los votos guardan el id del piloto, nunca el nombre. El bug más caro de 2026
-- (el formulario escribía "Hülkenberg" y el torneo "Hulkenberg": 16
-- predicciones mal puntuadas) no se puede repetir: no hay texto que comparar.

create table pilotos (
    id          serial primary key,
    temporada   smallint not null references temporadas,
    -- Identificador de la API (driverId de Jolpica/Ergast, ej. "max_verstappen").
    codigo_api  text not null,
    nombre      text not null,
    numero      smallint,
    equipo      text,
    unique (temporada, codigo_api),
    unique (temporada, nombre)
);

alter table temporadas
    add constraint temporadas_piloto_seguido_fk
    foreign key (piloto_seguido_id) references pilotos;

-- -----------------------------------------------------------------------------
-- Participantes
-- -----------------------------------------------------------------------------
--
-- Acá no hay mails. La identidad la maneja el login (auth.users en Supabase);
-- esta tabla solo sabe el apodo y a qué usuario corresponde.

create table participantes (
    id        uuid primary key default gen_random_uuid(),
    apodo     text not null unique,
    user_id   uuid unique,
    es_admin  boolean not null default false,
    activo    boolean not null default true,
    creado    timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- Carreras
-- -----------------------------------------------------------------------------
--
-- Cada carrera avanza sola por estos estados (ver avanzar_estados()):
--
--   programada -> abierta -> cerrada -> provisoria -> final
--                 (vota)     (largó)    (hay resultado) (sin cambios N horas)

create type estado_carrera as enum (
    'programada', 'abierta', 'cerrada', 'provisoria', 'final', 'cancelada'
);

create table carreras (
    id         serial primary key,
    temporada  smallint not null references temporadas,
    ronda      smallint not null,
    -- Nombre que usa la familia ("Países Bajos", no "Dutch Grand Prix").
    nombre     text not null,
    pais       char(2),
    -- Hora de largada en UTC. Es el corte de votos: exacto, lo aplica la base.
    largada    timestamptz,
    estado     estado_carrera not null default 'programada',
    unique (temporada, ronda),
    unique (temporada, nombre),
    check (estado = 'cancelada' or largada is not null)
);

-- -----------------------------------------------------------------------------
-- Votos
-- -----------------------------------------------------------------------------
--
-- Una boleta por participante y carrera. Nadie escribe esta tabla
-- directamente: se vota con la función votar(), que controla quién sos, que
-- la votación esté abierta y que la boleta sea válida.

create table votos (
    id                bigserial primary key,
    participante_id   uuid not null references participantes,
    carrera_id        int not null references carreras,
    -- top10[1] es el ganador predicho, top10[10] el décimo. Admite huecos
    -- solo para importar temporadas viejas; votar() exige los diez.
    top10             int[] not null check (cardinality(top10) = 10),
    vuelta_rapida_id  int references pilotos,
    pos_seguido       smallint check (pos_seguido between 1 and 40),
    creado            timestamptz not null default now(),
    actualizado       timestamptz not null default now(),
    unique (participante_id, carrera_id)
);

-- Cada alta, cambio o baja de un voto queda acá. En 2026, editar la planilla
-- después de la largada era invisible; acá queda marcado.
create table votos_auditoria (
    id                  bigserial primary key,
    voto_id             bigint not null,
    participante_id     uuid not null,
    carrera_id          int not null,
    operacion           text not null check (operacion in ('alta', 'cambio', 'baja')),
    antes               jsonb,
    despues             jsonb,
    despues_de_largada  boolean not null,
    quien               uuid,           -- auth.uid() de quien hizo el cambio
    cuando              timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- Resultados
-- -----------------------------------------------------------------------------

create table resultados (
    carrera_id        int primary key references carreras,
    vuelta_rapida_id  int references pilotos,
    fuente            text not null,
    -- Última vez que el resultado CAMBIÓ (no la última vez que se consultó).
    actualizado       timestamptz not null default now()
);

-- Clasificación: una fila por piloto. posicion null = no terminó.
create table resultados_pilotos (
    carrera_id  int not null references resultados on delete cascade,
    piloto_id   int not null references pilotos,
    posicion    smallint check (posicion > 0),
    primary key (carrera_id, piloto_id)
);

create unique index resultados_pilotos_posicion_unica
    on resultados_pilotos (carrera_id, posicion) where posicion is not null;

-- Cada vez que un resultado ya cargado cambia (penalidad de la FIA), queda
-- la versión anterior.
create table resultados_historial (
    id          bigserial primary key,
    carrera_id  int not null references carreras,
    anterior    jsonb not null,
    nuevo       jsonb not null,
    fuente      text not null,
    cuando      timestamptz not null default now()
);

-- -----------------------------------------------------------------------------
-- Puntajes
-- -----------------------------------------------------------------------------
--
-- Datos, no texto. En 2026 los logros se enteraban de qué acertó cada uno
-- leyendo el texto del detalle, y ese acoplamiento rompió tres logros sin que
-- nada fallara. Acá cada acierto es una fila con su tipo.

create type rubro as enum ('top10', 'vuelta_rapida', 'piloto_seguido');

create type tipo_acierto as enum (
    'exacto',          -- clavado
    'a_uno',           -- errado por un puesto
    'en_top10',        -- entró al top 10 en otro puesto
    'fuera',           -- no terminó en el top 10
    'errado',          -- vuelta rápida o piloto seguido no acertado
    'no_termino',      -- el piloto seguido abandonó
    'sin_prediccion',
    'sin_dato'         -- la API no informó el dato
);

create table puntajes (
    carrera_id         int not null references carreras on delete cascade,
    participante_id    uuid not null references participantes,
    rubro              rubro not null,
    -- Puesto de la boleta (1..10) para top10; 0 para los otros rubros.
    slot               smallint not null,
    piloto_id          int references pilotos,
    posicion_predicha  smallint,
    posicion_real      smallint,
    tipo               tipo_acierto not null,
    puntos             smallint not null,
    primary key (carrera_id, participante_id, rubro, slot)
);

-- -----------------------------------------------------------------------------
-- Eventos (cola de avisos)
-- -----------------------------------------------------------------------------
--
-- Todo lo que merece un aviso se anota acá, dentro de la misma transacción
-- que lo produjo. El que manda los WhatsApp lee lo pendiente y lo marca como
-- enviado: si el envío falla, el evento sigue pendiente y se reintenta; nunca
-- se pierde ni se manda dos veces.

create table eventos (
    id          bigserial primary key,
    tipo        text not null,
    carrera_id  int references carreras,
    datos       jsonb not null default '{}',
    creado      timestamptz not null default now(),
    enviado     timestamptz,
    intentos    smallint not null default 0,
    ultimo_error text
);

create index eventos_pendientes on eventos (creado) where enviado is null;
