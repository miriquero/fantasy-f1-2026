"""El nombre que escribe el formulario tiene que encontrarse en el resultado.

El calculo busca el piloto predicho dentro de las posiciones reales. Si la
grafia no coincide exactamente, el `.get` devuelve None y el sistema concluye
que el piloto "no termino en el top 10": cero puntos, sin ningun aviso.

Paso de verdad, 16 veces en 8 carreras de 2026, con dos nombres:

  - El formulario ofrece "Nico Hülkenberg" con dieresis; la lista del torneo
    lo escribe "Nico Hulkenberg". El resultado de la API se normaliza, el voto
    no, y nunca se cruzaban.
  - El formulario tiene "Olie Bearman" con una sola L.

El caso mas caro: en Hungria alguien puso a Bearman P9 y Bearman salio P9. Un
acierto exacto de 10 puntos contado como 0.

La propiedad que fijan estos tests: el resultado se normaliza, asi que el voto
tambien tiene que normalizarse. Los dos lados del cruce, con la misma funcion.
"""

import pandas as pd
import pytest

from f1.normalizacion import normalizar_piloto
from f1.scoring import acerto_posicion, calcular_puntos_y_detalles, cuantas_posiciones_exactas

VACIA = {c: "" for c in [
    "Primer puesto", "Segundo puesto", "Tercer puesto", "Cuarto puesto",
    "Quinto puesto", "Sexto puesto", "Séptimo puesto", "Octavo puesto",
    "Noveno puesto", "Décimo puesto", "Vuelta Rápida", "Franco Colapinto"]}


def fila(**kwargs):
    base = dict(VACIA)
    base.update(kwargs)
    return pd.Series(base)


# Como lo escribe el formulario -> como lo escribe la lista del torneo.
GRAFIAS = [
    ("Nico Hülkenberg", "Nico Hulkenberg"),
    ("Olie Bearman", "Ollie Bearman"),
    ("Sergio Pérez", "Sergio Perez"),
    ("Alexander Albon", "Alex Albon"),
    ("Andrea Kimi Antonelli", "Kimi Antonelli"),
]


@pytest.mark.parametrize("del_formulario, del_torneo", GRAFIAS)
def test_las_dos_grafias_son_el_mismo_piloto(del_formulario, del_torneo):
    assert normalizar_piloto(del_formulario) == del_torneo


@pytest.mark.parametrize("del_formulario, del_torneo", GRAFIAS)
def test_un_acierto_exacto_se_paga_aunque_el_formulario_lo_escriba_distinto(
        del_formulario, del_torneo):
    """El caso de Hungria: predicho P9, salio P9. Son 10 puntos."""
    puntos, detalle = calcular_puntos_y_detalles(
        fila(**{"Noveno puesto": del_formulario}), {del_torneo: 9}, "", 0)
    assert puntos == 10, detalle
    assert acerto_posicion(detalle, 9) is True
    assert cuantas_posiciones_exactas(detalle) == 1


@pytest.mark.parametrize("del_formulario, del_torneo", GRAFIAS)
def test_tampoco_se_pierde_el_acierto_parcial(del_formulario, del_torneo):
    """El caso de Singapur: predicho P9, salio P8. Es diferencia de uno."""
    puntos, detalle = calcular_puntos_y_detalles(
        fila(**{"Noveno puesto": del_formulario}), {del_torneo: 8}, "", 0)
    assert puntos == 5, detalle


@pytest.mark.parametrize("del_formulario, del_torneo", GRAFIAS)
def test_la_vuelta_rapida_se_paga_con_cualquier_grafia(del_formulario, del_torneo):
    puntos, detalle = calcular_puntos_y_detalles(
        fila(**{"Vuelta Rápida": del_formulario}), {}, del_torneo, 0)
    assert puntos == 10, detalle


def test_el_que_no_entro_al_top_10_sigue_dando_cero():
    """Normalizar no puede volverse un comodin: si el piloto no esta en el
    resultado, sigue siendo 0."""
    puntos, detalle = calcular_puntos_y_detalles(
        fila(**{"Noveno puesto": "Nico Hülkenberg"}), {"Max Verstappen": 1}, "", 0)
    assert puntos == 0
    assert "top 10" in detalle


def test_un_nombre_que_no_es_ningun_piloto_no_rompe_nada():
    puntos, detalle = calcular_puntos_y_detalles(
        fila(**{"Noveno puesto": "Juan Perez"}), {"Max Verstappen": 1}, "", 0)
    assert puntos == 0


# ------------------------------------------- el normalizador no puede explotar
# Ahora se lo llama en CADA celda de CADA voto, asi que cualquier entrada rara
# que antes no lo tocaba ahora pasa por ahi. Una celda con solo espacios lo
# hacia explotar con IndexError: el ultimo recurso parte el nombre por espacios
# para comparar apellidos, y de un string vacio no sale ningun apellido.
@pytest.mark.parametrize("basura", ["", "   ", "\t", "\n", "  \t ", None])
def test_una_celda_vacia_no_lo_hace_explotar(basura):
    assert not normalizar_piloto(basura)


def test_una_celda_de_espacios_no_se_cuenta_como_piloto():
    puntos, detalle = calcular_puntos_y_detalles(
        fila(**{"Noveno puesto": "   "}), {"Max Verstappen": 1}, "", 0)
    assert puntos == 0
    # no tiene que aparecer una linea de piloto inventada
    assert "Noveno" not in detalle
    assert ": No terminó" not in detalle
