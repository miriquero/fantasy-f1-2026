"""La vuelta rápida y Colapinto siempre aparecen en el detalle.

Antes solo salían al acertar. Como los pilotos del top 10 muestran su línea
aunque den 0 puntos, cuando estas dos desaparecían parecía que el sistema se
las había salteado, y los participantes reclamaban. Ahora salen siempre,
diciendo qué pusiste y qué pasó de verdad.

Mostrar más no puede cambiar el puntaje: eso también se testea acá.
"""

import pandas as pd
import pytest

from f1.scoring import calcular_puntos_y_detalles

VACIA = {c: "" for c in [
    "Primer puesto", "Segundo puesto", "Tercer puesto", "Cuarto puesto",
    "Quinto puesto", "Sexto puesto", "Séptimo puesto", "Octavo puesto",
    "Noveno puesto", "Décimo puesto", "Vuelta Rápida", "Franco Colapinto"]}


def fila(**kwargs):
    base = dict(VACIA)
    base.update(kwargs)
    return pd.Series(base)


def lineas(detalle):
    return detalle.split("<br>")


# --------------------------------------------------------------- vuelta rápida
def test_la_vuelta_rapida_aparece_aunque_se_haya_errado():
    _, d = calcular_puntos_y_detalles(
        fila(**{"Vuelta Rápida": "Lando Norris"}), {}, "Max Verstappen", 0)
    assert "Vuelta rápida: Lando Norris — la hizo Max Verstappen (0 pts)" in d


def test_la_vuelta_rapida_aparece_aunque_no_se_haya_cargado():
    _, d = calcular_puntos_y_detalles(fila(), {}, "Max Verstappen", 0)
    assert "Vuelta rápida: sin predicción — la hizo Max Verstappen (0 pts)" in d


def test_errar_la_vuelta_rapida_no_suma():
    p, _ = calcular_puntos_y_detalles(
        fila(**{"Vuelta Rápida": "Lando Norris"}), {}, "Max Verstappen", 0)
    assert p == 0


def test_acertar_la_vuelta_rapida_sigue_sumando_10():
    p, d = calcular_puntos_y_detalles(
        fila(**{"Vuelta Rápida": "Max Verstappen"}), {}, "Max Verstappen", 0)
    assert p == 10
    assert "Vuelta rápida: Max Verstappen (+10)" in d


# -------------------------------------------------------------------- Colapinto
def test_colapinto_aparece_aunque_se_haya_errado():
    _, d = calcular_puntos_y_detalles(
        fila(**{"Franco Colapinto": "Quinto Puesto"}), {}, "", 14)
    assert "Colapinto: pred P5, terminó P14 (0 pts)" in d


def test_colapinto_aparece_aunque_no_se_haya_cargado():
    _, d = calcular_puntos_y_detalles(fila(), {}, "", 14)
    assert "Colapinto: sin predicción (0 pts)" in d


def test_colapinto_por_uno_sigue_sumando_5():
    p, d = calcular_puntos_y_detalles(
        fila(**{"Franco Colapinto": "Décimo Quinto Puesto"}), {}, "", 14)
    assert p == 5
    assert "Colapinto: Diff 1 (pred P15, real P14) (+5)" in d


def test_si_colapinto_no_termino_se_dice_y_no_suma():
    # colapinto_real 0 significa que no figura en los resultados.
    p, d = calcular_puntos_y_detalles(
        fila(**{"Franco Colapinto": "Quinto Puesto"}), {}, "", 0)
    assert p == 0
    assert "no terminó la carrera" in d


# ------------------------------------------------------------------- invariante
@pytest.mark.parametrize("vr, col, real_vr, real_col, esperado", [
    ("",              "",                 "Verstappen", 14, 0),
    ("Norris",        "Quinto Puesto",    "Verstappen", 14, 0),
    ("Verstappen",    "Quinto Puesto",    "Verstappen", 14, 10),
    ("Norris",        "Décimo Cuarto Puesto", "Verstappen", 14, 10),
    ("Verstappen",    "Décimo Cuarto Puesto", "Verstappen", 14, 20),
])
def test_mostrar_mas_lineas_no_cambia_el_puntaje(vr, col, real_vr, real_col, esperado):
    p, d = calcular_puntos_y_detalles(
        fila(**{"Vuelta Rápida": vr, "Franco Colapinto": col}), {}, real_vr, real_col)
    assert p == esperado


def test_siempre_hay_exactamente_una_linea_de_cada_una():
    # Ni de más ni de menos, en cualquier combinación.
    for vr in ("", "Norris", "Verstappen"):
        for col in ("", "Quinto Puesto", "Décimo Cuarto Puesto"):
            _, d = calcular_puntos_y_detalles(
                fila(**{"Vuelta Rápida": vr, "Franco Colapinto": col}),
                {}, "Verstappen", 14)
            assert sum(1 for l in lineas(d) if l.startswith("Vuelta rápida:")) == 1
            assert sum(1 for l in lineas(d) if l.startswith("Colapinto:")) == 1
