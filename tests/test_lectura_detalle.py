"""Los logros leen el texto que escribe el cálculo. Que no se separen.

Ese acoplamiento ya rompió tres cosas sin que fallara nada:

1. Al reformatear "Colapinto: EXACTO" a "Colapinto: Exacto en P9", el logro
   "Hincha de Franco" quedó inalcanzable para siempre.
2. Esa misma línea empezó a contarse como acierto de posición de un piloto,
   porque contiene "Exacto en P9", inflando "Adivino" y "Apostador Nato".
3. Buscar "Exacto en P1" con `in` también matchea "Exacto en P10", así que
   los aciertos del décimo puesto se contaban como aciertos del ganador.

Los tres daban resultados plausibles. Nadie se entera de que un logro está mal
hasta que alguien mira la tabla y le parece raro.

El último test es el importante: no fija el texto, sino que verifica que el
lector y el escritor coincidan sobre datos generados de verdad.
"""

import pandas as pd
import pytest

from f1.scoring import (
    acerto_colapinto,
    acerto_posicion,
    calcular_puntos_y_detalles,
    cuantas_posiciones_exactas,
    lineas_de_pilotos,
)

VACIA = {c: "" for c in [
    "Primer puesto", "Segundo puesto", "Tercer puesto", "Cuarto puesto",
    "Quinto puesto", "Sexto puesto", "Séptimo puesto", "Octavo puesto",
    "Noveno puesto", "Décimo puesto", "Vuelta Rápida", "Franco Colapinto"]}


def fila(**kwargs):
    base = dict(VACIA)
    base.update(kwargs)
    return pd.Series(base)


# --------------------------------------------------- P10 no es P1
def test_acertar_p10_no_cuenta_como_acertar_p1():
    detalle = "Yuki Tsunoda: Exacto en P10 (+10)"
    assert acerto_posicion(detalle, 10) is True
    assert acerto_posicion(detalle, 1) is False


def test_cada_posicion_se_reconoce_sola():
    detalle = "<br>".join(f"Piloto{p}: Exacto en P{p} (+10)" for p in (1, 2, 10))
    for p in (1, 2, 10):
        assert acerto_posicion(detalle, p) is True
    for p in (3, 4, 5, 6, 7, 8, 9):
        assert acerto_posicion(detalle, p) is False


# ------------------------------------------- Colapinto no es un piloto del top 10
def test_el_acierto_de_colapinto_no_cuenta_como_posicion_del_top10():
    detalle = "Colapinto: Exacto en P9 (+10)"
    assert acerto_colapinto(detalle) is True
    assert acerto_posicion(detalle, 9) is False
    assert cuantas_posiciones_exactas(detalle) == 0


def test_la_vuelta_rapida_tampoco_se_cuenta_como_posicion():
    detalle = "Vuelta rápida: Max Verstappen (+10)"
    assert lineas_de_pilotos(detalle) == []
    assert cuantas_posiciones_exactas(detalle) == 0


def test_se_distingue_el_piloto_Colapinto_de_la_prediccion_de_Colapinto():
    # "Franco Colapinto" puede estar en el top 10 Y tener su propia línea.
    # Son dos aciertos distintos y se cuentan por separado.
    detalle = ("Franco Colapinto: Exacto en P9 (+10)<br>"
               "Colapinto: Exacto en P9 (+10)")
    assert cuantas_posiciones_exactas(detalle) == 1
    assert acerto_posicion(detalle, 9) is True
    assert acerto_colapinto(detalle) is True


def test_errar_colapinto_no_cuenta_como_acierto():
    for detalle in ("Colapinto: pred P5, terminó P14 (0 pts)",
                    "Colapinto: sin predicción (0 pts)",
                    "Colapinto: Diff 1 (pred P15, real P14) (+5)",
                    "Colapinto: pred P5 — no terminó la carrera (0 pts)"):
        assert acerto_colapinto(detalle) is False, detalle


# ------------------------------------------- el lector y el escritor coinciden
@pytest.mark.parametrize("colapinto_pred, colapinto_real, acierta", [
    ("Décimo Puesto", 10, True),
    ("Décimo Puesto", 11, False),
    ("", 10, False),
    ("Quinto Puesto", 0, False),
])
def test_el_lector_coincide_con_lo_que_escribe_el_calculo(colapinto_pred, colapinto_real, acierta):
    """Si alguien cambia la redacción de la línea, esto falla acá y no en
    silencio dentro de un logro tres meses después."""
    _, detalle = calcular_puntos_y_detalles(
        fila(**{"Franco Colapinto": colapinto_pred}), {}, "", colapinto_real)
    assert acerto_colapinto(detalle) is acierta


def test_las_posiciones_exactas_que_escribe_el_calculo_se_leen_igual():
    reales = {"Max Verstappen": 1, "Lando Norris": 2, "Yuki Tsunoda": 10}
    _, detalle = calcular_puntos_y_detalles(
        fila(**{"Primer puesto": "Max Verstappen",
                "Segundo puesto": "Lando Norris",
                "Décimo puesto": "Yuki Tsunoda",
                "Franco Colapinto": "Décimo Puesto"}),
        reales, "", 10)

    # Tres exactos de pilotos, mas Colapinto aparte.
    assert cuantas_posiciones_exactas(detalle) == 3
    assert acerto_posicion(detalle, 1) is True
    assert acerto_posicion(detalle, 2) is True
    assert acerto_posicion(detalle, 10) is True
    assert acerto_posicion(detalle, 3) is False
    assert acerto_colapinto(detalle) is True
