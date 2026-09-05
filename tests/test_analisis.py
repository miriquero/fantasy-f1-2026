"""Proyección al título y cara a cara.

Son cuentas cerradas, no pronósticos, así que se pueden verificar exactamente.
"""

import pandas as pd
import pytest

from f1.analisis import (
    MAXIMO_POR_CARRERA,
    cara_a_cara,
    carreras_totales,
    proyeccion_titulo,
)
from f1.config import COL_PUESTOS


def _acumulado(pares):
    df = pd.DataFrame(pares, columns=["Participante", "Puntos"])
    df["Posición"] = range(1, len(df) + 1)
    return df


def test_el_maximo_por_carrera_coincide_con_las_reglas_de_puntaje():
    # 10 aciertos exactos del top 10, mas la vuelta rápida, mas Colapinto.
    # Si cambia el puntaje y esto no, la proyección miente.
    assert MAXIMO_POR_CARRERA == len(COL_PUESTOS) * 10 + 10 + 10


def test_el_torneo_tiene_las_carreras_del_calendario():
    # Las tachadas no cuentan: no se juegan.
    assert carreras_totales() == 22


def test_el_puntero_no_tiene_diferencia():
    proy = proyeccion_titulo(_acumulado([("ana", 100), ("beto", 60)]), carreras_jugadas=21)
    assert proy[0]["es_lider"] is True
    assert proy[0]["diferencia"] == 0
    assert proy[0]["vivo"] is True


def test_queda_sin_chances_quien_no_llega_ni_ganando_todo():
    # Falta 1 carrera: se pueden sumar 120 puntos como máximo.
    proy = proyeccion_titulo(
        _acumulado([("ana", 500), ("beto", 400), ("caro", 300)]), carreras_jugadas=21)
    por_nombre = {p["participante"]: p for p in proy}
    assert por_nombre["beto"]["vivo"] is True      # está a 100, alcanza
    assert por_nombre["caro"]["vivo"] is False     # está a 200, no alcanza


def test_el_limite_exacto_todavia_cuenta_como_vivo():
    # Justo a 120 con una carrera por delante: empata, y empatar es llegar.
    proy = proyeccion_titulo(
        _acumulado([("ana", 500), ("beto", 500 - MAXIMO_POR_CARRERA)]), carreras_jugadas=21)
    assert proy[1]["vivo"] is True

    proy = proyeccion_titulo(
        _acumulado([("ana", 500), ("beto", 500 - MAXIMO_POR_CARRERA - 1)]), carreras_jugadas=21)
    assert proy[1]["vivo"] is False


def test_sin_carreras_jugadas_no_se_rompe():
    assert proyeccion_titulo(pd.DataFrame(columns=["Participante", "Puntos"]), 0) == []


def _rankings(filas):
    return pd.DataFrame(filas, columns=["Carrera", "Participante", "Puntos"])


def test_el_cara_a_cara_cuenta_ganadas_perdidas_y_empatadas():
    datos = _rankings([
        ("Italia", "ana", 50), ("Italia", "beto", 30),
        ("Madrid", "ana", 10), ("Madrid", "beto", 40),
        ("Qatar", "ana", 20), ("Qatar", "beto", 20),
    ])
    duelo = {d["rival"]: d for d in cara_a_cara(datos)["ana"]}["beto"]
    assert (duelo["gano"], duelo["perdio"], duelo["empato"]) == (1, 1, 1)


def test_solo_cuentan_las_carreras_que_jugaron_LOS_DOS():
    # beto no corrió en Madrid. Esa carrera no puede contar como derrota suya:
    # en el torneo real hay gente que se sumó tarde y jugó 5 de 9 carreras.
    datos = _rankings([
        ("Italia", "ana", 50), ("Italia", "beto", 30),
        ("Madrid", "ana", 90),
    ])
    duelo = {d["rival"]: d for d in cara_a_cara(datos)["ana"]}["beto"]
    assert duelo["gano"] + duelo["perdio"] + duelo["empato"] == 1


def test_el_cara_a_cara_es_simetrico():
    datos = _rankings([
        ("Italia", "ana", 50), ("Italia", "beto", 30),
        ("Madrid", "ana", 10), ("Madrid", "beto", 40),
    ])
    duelos = cara_a_cara(datos)
    de_ana = {d["rival"]: d for d in duelos["ana"]}["beto"]
    de_beto = {d["rival"]: d for d in duelos["beto"]}["ana"]
    assert de_ana["gano"] == de_beto["perdio"]
    assert de_ana["perdio"] == de_beto["gano"]


def test_nadie_se_enfrenta_a_si_mismo():
    datos = _rankings([("Italia", "ana", 50), ("Italia", "beto", 30)])
    for uno, rivales in cara_a_cara(datos).items():
        assert all(r["rival"] != uno for r in rivales)
