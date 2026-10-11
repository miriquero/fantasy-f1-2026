"""El validador no puede rechazar un resultado real de la temporada.

Es un portero: si dice que resultados.json esta mal, el calculo no corre y no
puntua NADIE en esa carrera. Por eso un limite de mas en el validador no es un
detalle, es el torneo entero parado.

Paso de verdad en Singapur 2026. La cota de la posicion de Colapinto estaba
escrita a mano en 20, que era el tamano de la grilla de temporadas anteriores.
En 2026 corren 11 equipos: clasificaron 22 autos y Colapinto termino 21. El
validador lo marco como "valor invalido" y la carrera no se pudo calcular.

Estos tests fijan la unica propiedad que importa: cualquier posicion que exista
de verdad en la grilla tiene que pasar.
"""

import pytest

from f1.config import PILOTOS
from f1.validacion import MAX_POSICION, validar_resultados


def resultado(colapinto):
    """Una carrera valida, con la posicion de Colapinto como unica variable."""
    return {"Singapur": {
        "resultado_carrera": PILOTOS[:11],
        "vuelta_rapida": PILOTOS[0],
        "colapinto": colapinto,
    }}


# --------------------------------------------- la grilla entera tiene que entrar
def test_la_cota_cubre_a_todos_los_pilotos_del_torneo():
    """Si el torneo lista 23 pilotos, el puesto 23 tiene que ser valido: no se
    puede listar a alguien que el validador despues rechaza."""
    assert MAX_POSICION >= len(PILOTOS)


@pytest.mark.parametrize("pos", [21, 22])
def test_las_posiciones_que_antes_rompian_ahora_pasan(pos):
    """P21 fue el caso real de Singapur; P22 es el ultimo auto de una grilla de
    11 equipos."""
    assert validar_resultados(resultado(pos)) is True


def test_toda_posicion_de_la_grilla_es_valida():
    for pos in range(0, len(PILOTOS) + 1):
        assert validar_resultados(resultado(pos)) is True, f"rechazo P{pos}"


# --------------------------------------------- pero sigue siendo un portero
def test_cero_sigue_valiendo_para_el_que_no_termino():
    assert validar_resultados(resultado(0)) is True


def test_una_posicion_que_no_existe_se_rechaza():
    """La cota tiene que seguir existiendo: un numero imposible es un error de
    carga y conviene que avise, no que lo deje pasar."""
    assert validar_resultados(resultado(MAX_POSICION + 1)) is False


def test_una_posicion_negativa_se_rechaza():
    assert validar_resultados(resultado(-1)) is False


def test_lo_que_no_es_numero_se_rechaza():
    assert validar_resultados(resultado("no termino")) is False


def test_el_numero_como_texto_se_acepta():
    """La API devuelve la posicion como string."""
    assert validar_resultados(resultado("21")) is True
