"""
La prueba de oro: la temporada 2026 entera, cargada en la base nueva, tiene
que dar exactamente los mismos puntos que dio el sistema de 2026. Carrera por
carrera y participante por participante.

Si este test falla, el sistema nuevo calcula distinto que el viejo, y eso se
resuelve antes de que la familia lo vea, no después.
"""

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from cargar_temporada import cargar  # noqa: E402

DATOS = json.loads((RAIZ / "datos_2026" / "temporada_2026.json").read_text(encoding="utf-8"))


@pytest.fixture
def temporada_2026(db):
    cargar(db, DATOS)
    return db


def test_cada_carrera_da_los_mismos_puntos_que_en_2026(temporada_2026):
    filas = temporada_2026.execute(
        "select carrera, apodo, puntos from puntos_por_carrera where temporada = 2026"
    ).fetchall()
    obtenido = {}
    for carrera, apodo, puntos in filas:
        obtenido.setdefault(carrera, {})[apodo] = puntos

    assert obtenido == DATOS["esperado"]


def test_el_ranking_final_es_el_mismo(temporada_2026):
    esperado = {}
    for por_participante in DATOS["esperado"].values():
        for apodo, puntos in por_participante.items():
            esperado[apodo] = esperado.get(apodo, 0) + puntos

    filas = temporada_2026.execute(
        "select apodo, puntos from ranking where temporada = 2026").fetchall()
    assert dict(filas) == esperado


def test_se_cargaron_todos_los_votos_y_resultados(temporada_2026):
    n_votos = temporada_2026.execute("select count(*) from votos").fetchone()[0]
    n_res = temporada_2026.execute("select count(*) from resultados").fetchone()[0]
    assert n_votos == len(DATOS["votos"])
    assert n_res == len(DATOS["resultados"])


def test_la_carga_no_deja_avisos_pendientes(temporada_2026):
    # Cargar la temporada vieja no puede mandar 17 WhatsApp de carreras de
    # hace meses.
    pendientes = temporada_2026.execute(
        "select count(*) from eventos where enviado is null").fetchone()[0]
    assert pendientes == 0
