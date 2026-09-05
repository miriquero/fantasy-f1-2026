"""Que un piloto inesperado no frene la temporada entera.

La API devuelve los nombres como se le ocurre, y en una temporada corre gente
que no estaba en la lista al empezar (suplentes, debutantes, un cambio de
butaca). Antes cualquiera de esas dos cosas cortaba el `main()` y el ranking
dejaba de actualizarse hasta que alguien editara el codigo.
"""

import pytest

from f1.normalizacion import normalizar_piloto
from f1.validacion import validar_resultados


@pytest.mark.parametrize("de_la_api, canonico", [
    ("Oliver Bearman", "Ollie Bearman"),
    ("Andrea Kimi Antonelli", "Kimi Antonelli"),
    ("Alexander Albon", "Alex Albon"),
    ("Gabriel Bortoleto", "Gabriel Bortoletto"),
    ("Sergio Pérez", "Sergio Perez"),
    ("Nico Hülkenberg", "Nico Hulkenberg"),
])
def test_variantes_de_la_api_llegan_al_nombre_canonico(de_la_api, canonico):
    assert normalizar_piloto(de_la_api) == canonico


def test_un_nombre_nuevo_se_resuelve_por_apellido():
    # Sin alias cargado: la API podria empezar a mandar el nombre completo.
    assert normalizar_piloto("Francisco Colapinto") == "Franco Colapinto"
    assert normalizar_piloto("Maximilian Verstappen") == "Max Verstappen"


def test_un_piloto_realmente_desconocido_se_deja_como_esta():
    assert normalizar_piloto("Ayumu Iwasa") == "Ayumu Iwasa"


def _carrera(resultado=None, vuelta_rapida="Max Verstappen"):
    base = ["Max Verstappen", "Charles Leclerc", "Lewis Hamilton", "Oscar Piastri",
            "Lando Norris", "George Russell", "Kimi Antonelli", "Pierre Gasly",
            "Carlos Sainz", "Alex Albon", "Esteban Ocon"]
    return {"Carrera": {"resultado_carrera": resultado or base,
                        "vuelta_rapida": vuelta_rapida,
                        "colapinto": "12"}}


def test_un_suplente_desconocido_no_frena_el_ranking():
    # Antes esto devolvia False y main() hacia return: se dejaba de generar el
    # ranking de TODA la temporada, no solo el de esa carrera.
    resultado = _carrera()["Carrera"]["resultado_carrera"][:]
    resultado[6] = "Ayumu Iwasa"
    assert validar_resultados(_carrera(resultado=resultado)) is True


def test_una_vuelta_rapida_de_un_desconocido_no_frena_el_ranking():
    assert validar_resultados(_carrera(vuelta_rapida="Ayumu Iwasa")) is True


def test_pero_un_archivo_realmente_roto_sigue_frenando():
    # No hay que aflojar tanto la validacion que deje pasar cualquier cosa.
    assert validar_resultados({"Carrera": {"vuelta_rapida": "Max Verstappen"}}) is False
    assert validar_resultados({"Carrera": {"resultado_carrera": "no es una lista",
                                           "vuelta_rapida": "Max Verstappen",
                                           "colapinto": "12"}}) is False
    assert validar_resultados({}) is False
