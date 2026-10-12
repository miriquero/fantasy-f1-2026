"""
Reglas de la votación: quién puede votar, qué y hasta cuándo. Todo esto lo
hace cumplir la base, así que se prueba entrando con los mismos permisos que
tiene la página.
"""

import uuid

import psycopg
import pytest
from psycopg.types.json import Jsonb


@pytest.fixture
def torneo(db):
    """Una temporada chica: 12 pilotos, 2 participantes, una carrera abierta."""
    db.execute("insert into temporadas (anio) values (2027)")
    ids = [db.execute(
        "insert into pilotos (temporada, codigo_api, nombre) values (2027, %s, %s) returning id",
        (f"p{i}", f"Piloto {i}")).fetchone()[0] for i in range(1, 13)]
    db.execute("update temporadas set piloto_seguido_id = %s", (ids[11],))

    usuarios = {}
    for apodo in ("ana", "beto"):
        uid = uuid.uuid4()
        db.execute("insert into participantes (apodo, user_id) values (%s, %s)", (apodo, uid))
        usuarios[apodo] = uid

    carrera = db.execute(
        "insert into carreras (temporada, ronda, nombre, largada, estado) "
        "values (2027, 1, 'Australia', now() + interval '2 days', 'abierta') returning id"
    ).fetchone()[0]
    return {"pilotos": ids, "usuarios": usuarios, "carrera": carrera, "db": db}


def votar(como, t, apodo, top10=None, vuelta=None, seguido=12):
    top10 = top10 or t["pilotos"][:10]
    vuelta = vuelta or t["pilotos"][0]
    return como(t["usuarios"][apodo]).execute(
        "select (votar(%s, %s, %s, %s::smallint)).id",
        (t["carrera"], top10, vuelta, seguido))


def test_un_participante_vota(como, torneo):
    votar(como, torneo, "ana")
    n = torneo["db"].execute("select count(*) from votos").fetchone()[0]
    assert n == 1


def test_puede_cambiar_el_voto_hasta_la_largada_y_queda_registrado(como, torneo):
    votar(como, torneo, "ana")
    otro = list(reversed(torneo["pilotos"][:10]))
    votar(como, torneo, "ana", top10=otro)

    db = torneo["db"]
    assert db.execute("select top10 from votos").fetchone()[0] == otro
    ops = [r[0] for r in db.execute(
        "select operacion from votos_auditoria order by id").fetchall()]
    assert ops == ["alta", "cambio"]


def test_sin_usuario_no_se_vota(como, torneo):
    with pytest.raises(psycopg.Error):
        como(None).execute("select votar(%s, %s, %s, 1::smallint)",
                           (torneo["carrera"], torneo["pilotos"][:10], torneo["pilotos"][0]))


def test_no_se_vota_despues_de_la_largada(como, torneo):
    # Aunque el estado siga en "abierta" (el reloj no corrió todavía), la
    # largada manda: el corte no depende de que ningún proceso llegue a tiempo.
    torneo["db"].execute("update carreras set largada = now() - interval '1 minute'")
    with pytest.raises(psycopg.errors.RaiseException, match="cerrada"):
        votar(como, torneo, "ana")


def test_no_se_repite_un_piloto(como, torneo):
    p = torneo["pilotos"]
    with pytest.raises(psycopg.Error, match="mismo piloto"):
        votar(como, torneo, "ana", top10=[p[0]] * 2 + p[2:10])


def test_hay_que_completar_los_diez(como, torneo):
    with pytest.raises(psycopg.Error, match="diez"):
        votar(como, torneo, "ana", top10=torneo["pilotos"][:9])


def test_la_pagina_no_puede_escribir_la_tabla_directo(como, torneo):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        como(torneo["usuarios"]["ana"]).execute(
            "update votos set top10 = top10")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        como(torneo["usuarios"]["ana"]).execute(
            "update carreras set largada = now() + interval '1 year'")


def test_los_votos_ajenos_se_ven_recien_desde_la_largada(como, torneo):
    votar(como, torneo, "ana")
    beto = como(torneo["usuarios"]["beto"])
    assert beto.execute("select count(*) from votos")[0][0] == 0

    torneo["db"].execute("update carreras set largada = now() - interval '1 minute'")
    assert beto.execute("select count(*) from votos")[0][0] == 1


def test_los_mails_no_son_visibles(como, torneo):
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        como(None).execute("select user_id from participantes")


def test_un_cambio_despues_de_la_largada_genera_aviso(torneo):
    # Esto en 2026 era invisible: alguien editaba la planilla después de la
    # carrera y no quedaba rastro.
    db = torneo["db"]
    pid = db.execute("select id from participantes where apodo = 'ana'").fetchone()[0]
    db.execute("update carreras set largada = now() - interval '1 hour'")
    db.execute("insert into votos (participante_id, carrera_id, top10) values (%s, %s, %s)",
               (pid, torneo["carrera"], torneo["pilotos"][:10]))
    tipo, datos = db.execute("select tipo, datos from eventos").fetchone()
    assert tipo == "voto_fuera_de_termino"
    assert datos["apodo"] == "ana"
