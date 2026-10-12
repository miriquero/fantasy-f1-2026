"""
El ciclo de vida de una carrera y el cálculo de puntos, con casos armados a
mano para cada regla.
"""

import uuid

import pytest
from psycopg.types.json import Jsonb


@pytest.fixture
def base(db):
    db.execute("insert into temporadas (anio) values (2027)")
    ids = {}
    for i in range(1, 23):
        ids[i] = db.execute(
            "insert into pilotos (temporada, codigo_api, nombre) values (2027, %s, %s) returning id",
            (f"p{i}", f"Piloto {i}")).fetchone()[0]
    db.execute("update temporadas set piloto_seguido_id = %s", (ids[22],))
    db.execute("insert into participantes (apodo, user_id) values ('ana', %s)", (uuid.uuid4(),))
    return db, ids


def nueva_carrera(db, largada_sql, estado="programada", ronda=1):
    return db.execute(
        f"insert into carreras (temporada, ronda, nombre, largada, estado) "
        f"values (2027, %s, %s, {largada_sql}, %s) returning id",
        (ronda, f"Carrera {ronda}", estado)).fetchone()[0]


def estado(db, carrera):
    return db.execute("select estado::text from carreras where id = %s", (carrera,)).fetchone()[0]


def tipos_de_eventos(db):
    return [r[0] for r in db.execute("select tipo from eventos order by id").fetchall()]


# --- Ciclo de vida -----------------------------------------------------------

def test_se_abre_sola_dias_antes(base):
    db, _ = base
    lejos = nueva_carrera(db, "now() + interval '10 days'", ronda=1)
    cerca = nueva_carrera(db, "now() + interval '3 days'", ronda=2)
    db.execute("select avanzar_estados()")
    assert estado(db, lejos) == "programada"
    assert estado(db, cerca) == "abierta"
    assert "votacion_abierta" in tipos_de_eventos(db)


def test_se_cierra_sola_en_la_largada(base):
    db, _ = base
    c = nueva_carrera(db, "now() - interval '1 minute'", estado="abierta")
    db.execute("select avanzar_estados()")
    assert estado(db, c) == "cerrada"
    (datos,) = db.execute("select datos from eventos where tipo = 'votacion_cerrada'").fetchone()
    assert datos["no_votaron"] == ["ana"]


def test_si_se_pierden_corridas_la_siguiente_pone_todo_al_dia(base):
    # Una carrera que se abrió y largó sin que el reloj corriera queda
    # cerrada, no abierta.
    db, _ = base
    c = nueva_carrera(db, "now() - interval '1 hour'")
    db.execute("select avanzar_estados()")
    assert estado(db, c) == "cerrada"


def test_correr_dos_veces_no_duplica_avisos(base):
    db, _ = base
    nueva_carrera(db, "now() + interval '30 minutes'")
    db.execute("select avanzar_estados()")
    antes = tipos_de_eventos(db)
    db.execute("select avanzar_estados()")
    assert tipos_de_eventos(db) == antes
    assert antes == ["votacion_abierta", "recordatorio_24h", "recordatorio_1h"]


def test_sin_pendientes_no_hay_recordatorio(base):
    db, ids = base
    c = nueva_carrera(db, "now() + interval '30 minutes'", estado="abierta")
    pid = db.execute("select id from participantes").fetchone()[0]
    db.execute("insert into votos (participante_id, carrera_id, top10, vuelta_rapida_id, pos_seguido) "
               "values (%s, %s, %s, %s, 5)", (pid, c, [ids[i] for i in range(1, 11)], ids[1]))
    db.execute("select avanzar_estados()")
    assert tipos_de_eventos(db) == []


# --- Puntos ------------------------------------------------------------------

def clasificacion(ids, orden, seguido_pos=None):
    """orden: lista de números de piloto en orden de llegada."""
    filas = [{"piloto": f"p{n}", "posicion": pos} for pos, n in enumerate(orden, 1)]
    if seguido_pos is not None or 22 not in orden:
        filas.append({"piloto": "p22", "posicion": seguido_pos})
    return Jsonb(filas)


@pytest.fixture
def carrera_con_voto(base):
    db, ids = base
    c = nueva_carrera(db, "now() - interval '2 hours'", estado="cerrada")
    pid = db.execute("select id from participantes").fetchone()[0]
    # Boleta: p1..p10 en orden, vuelta rápida p1, seguido P15.
    db.execute("insert into votos (participante_id, carrera_id, top10, vuelta_rapida_id, pos_seguido) "
               "values (%s, %s, %s, %s, 15)", (pid, c, [ids[i] for i in range(1, 11)], ids[1]))
    return db, c


def puntos(db, c):
    return {(r, s): (t, p) for r, s, t, p in db.execute(
        "select rubro::text, slot, tipo::text, puntos from puntajes where carrera_id = %s", (c,))}


def test_reglas_del_top10(carrera_con_voto):
    db, c = carrera_con_voto
    # Llegada: p1 P1 (exacto), p3 P2 y p2 P3 (a uno), p4..p9 en orden,
    # p10 termina P11 (fuera: el top 10 es el corte), p11 P10.
    orden = [1, 3, 2, 4, 5, 6, 7, 8, 9, 11, 10]
    db.execute("select registrar_resultado(%s, %s, 'p1', 'test')",
               (c, clasificacion(None, orden, 15)))
    p = puntos(db, c)
    assert p[("top10", 1)] == ("exacto", 10)
    assert p[("top10", 2)] == ("a_uno", 5)
    assert p[("top10", 3)] == ("a_uno", 5)
    assert p[("top10", 10)] == ("fuera", 0)
    assert p[("vuelta_rapida", 0)] == ("exacto", 10)
    assert p[("piloto_seguido", 0)] == ("exacto", 10)


def test_en_top10_paga_uno(carrera_con_voto):
    db, c = carrera_con_voto
    orden = [5, 2, 3, 4, 1, 6, 7, 8, 9, 10]   # p1 predicho P1 termina P5
    db.execute("select registrar_resultado(%s, %s, 'p2', 'test')",
               (c, clasificacion(None, orden, 16)))
    p = puntos(db, c)
    assert p[("top10", 1)] == ("en_top10", 1)
    assert p[("vuelta_rapida", 0)] == ("errado", 0)
    assert p[("piloto_seguido", 0)] == ("a_uno", 5)


def test_seguido_que_abandona_no_paga(carrera_con_voto):
    db, c = carrera_con_voto
    db.execute("select registrar_resultado(%s, %s, null, 'test')",
               (c, clasificacion(None, list(range(1, 11)), None)))
    p = puntos(db, c)
    assert p[("piloto_seguido", 0)] == ("no_termino", 0)
    assert p[("vuelta_rapida", 0)] == ("sin_dato", 0)


def test_las_reglas_se_cambian_con_datos(carrera_con_voto):
    # Si para 2027 la familia decide que el exacto vale 12, es una fila.
    db, c = carrera_con_voto
    db.execute("update temporadas set pts_exacto = 12")
    db.execute("select registrar_resultado(%s, %s, null, 'test')",
               (c, clasificacion(None, list(range(1, 11)), 12)))
    assert puntos(db, c)[("top10", 1)] == ("exacto", 12)


# --- Correcciones de la FIA --------------------------------------------------

def test_una_penalidad_recalcula_y_avisa(carrera_con_voto):
    db, c = carrera_con_voto
    orden = list(range(1, 11))
    assert db.execute("select registrar_resultado(%s, %s, 'p1', 'jolpica')",
                      (c, clasificacion(None, orden, 15))).fetchone()[0] == "nuevo"
    total = lambda: db.execute("select sum(puntos) from puntajes where carrera_id = %s",
                               (c,)).fetchone()[0]
    antes = total()

    # Misma consulta otra vez: nada cambia, nada se avisa.
    assert db.execute("select registrar_resultado(%s, %s, 'p1', 'jolpica')",
                      (c, clasificacion(None, orden, 15))).fetchone()[0] == "sin_cambios"

    # Penalidad: p1 pierde la victoria.
    orden_nuevo = [2, 1] + list(range(3, 11))
    assert db.execute("select registrar_resultado(%s, %s, 'p1', 'jolpica')",
                      (c, clasificacion(None, orden_nuevo, 15))).fetchone()[0] == "corregido"
    assert total() < antes
    assert db.execute("select count(*) from resultados_historial").fetchone()[0] == 1
    assert [e for e in tipos_de_eventos(db) if e.startswith("resultado")] \
        == ["resultado", "resultado_corregido"]


def test_un_piloto_nuevo_se_agrega_solo(carrera_con_voto):
    db, c = carrera_con_voto
    filas = [{"piloto": f"p{n}", "posicion": n} for n in range(1, 10)]
    filas.append({"piloto": "reemplazo", "nombre": "Piloto Reemplazo", "posicion": 10})
    db.execute("select registrar_resultado(%s, %s, null, 'test')", (c, Jsonb(filas)))
    assert db.execute("select nombre from pilotos where codigo_api = 'reemplazo'").fetchone()[0] \
        == "Piloto Reemplazo"


def test_queda_definitiva_cuando_no_cambia_mas(carrera_con_voto):
    db, c = carrera_con_voto
    db.execute("select registrar_resultado(%s, %s, null, 'test')",
               (c, clasificacion(None, list(range(1, 11)), 13)))
    assert estado(db, c) == "provisoria"
    db.execute("update resultados set actualizado = now() - interval '49 hours'")
    db.execute("select avanzar_estados()")
    assert estado(db, c) == "final"
