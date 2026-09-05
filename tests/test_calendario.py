"""Coherencia del calendario entre las tres partes que lo usan.

Los errores que cubren estos tests no rompian nada de forma visible: el
ranking se generaba igual, pero con la carrera equivocada o en el orden
equivocado. Por eso hace falta chequearlos explicitamente.
"""

import re

import pytest

import fetch_resultados
import fetch_votos
from f1.calendario import get_orden_carreras
from f1.config import CALENDARIO
from f1.normalizacion import normalizar_nombre_carrera


def carreras_del_torneo():
    """Nombres crudos de las carreras que se juegan (sin las tachadas)."""
    return [re.sub(r"<[^>]+>", "", e["Carrera"]).strip()
            for e in CALENDARIO if e.get("FechaISO")]


def test_el_orden_del_calendario_usa_los_mismos_nombres_que_el_ranking():
    # get_orden_carreras() armaba los nombres con .capitalize(), que da
    # "Gran bretaña" y "Las vegas". Esos no coincidian con los nombres
    # normalizados del resto del pipeline, asi que esas carreras se caian del
    # orden del calendario y quedaban al final: el historial de posiciones las
    # trataba como si hubieran corrido despues de las que en realidad las
    # siguieron.
    for nombre in get_orden_carreras():
        assert nombre == normalizar_nombre_carrera(nombre), (
            f"'{nombre}' no sobrevive al normalizador; no va a matchear con "
            f"los nombres de carrera del ranking")


def test_todas_las_carreras_tienen_corte_de_votos():
    # Si una carrera no matchea ningun corte, corte_carrera() devuelve None y
    # se aceptan votos despues de la largada.
    for nombre in carreras_del_torneo():
        assert fetch_votos.corte_carrera(nombre) is not None, (
            f"'{nombre}' se quedo sin horario de corte")


@pytest.mark.parametrize("escrito", ["Azerbaiyán", "Azerbaiyan", "AZERBAIYN",
                                     "azerbaiyan", "Azerbaiyán "])
def test_azerbaiyan_converge_escribase_como_se_escriba(escrito):
    # Al calendario le faltaba una letra ("AZERBAIYN"). Si el Google Form
    # mandaba la grafia correcta, el CSV normalizaba distinto que la clave de
    # resultados.json y la carrera no puntuaba a nadie, en silencio.
    assert normalizar_nombre_carrera(escrito) == "Azerbaiyan"


def test_los_rounds_salen_de_la_api_y_no_de_una_tabla_a_mano():
    # La FIA sumo el "Bahrain Grand Prix in Malaysia" como round 16 y corrio
    # todo lo posterior un lugar. Con los numeros escritos a mano, en octubre
    # el script hubiera pedido la carrera equivocada y guardado esos
    # resultados con el nombre de otra.
    assert not hasattr(fetch_resultados, "NOMBRE_A_ROUND"), (
        "volvio la tabla de rounds escrita a mano")

    calendario_api = {
        "2026-10-04": (16, "Bahrain Grand Prix in Malaysia"),
        "2026-10-11": (17, "Singapore Grand Prix"),
        "2026-12-06": (23, "Abu Dhabi Grand Prix"),
    }
    mapa = fetch_resultados.rounds_del_torneo(calendario_api)
    assert mapa["SINGAPUR"] == 17
    assert mapa["ABU DHABI"] == 23
    # La de Malasia no esta en el torneo, asi que no debe aparecer.
    assert len(mapa) == 2


def test_una_carrera_que_la_api_no_conoce_se_saltea_sin_romper(capsys):
    mapa = fetch_resultados.rounds_del_torneo({"2026-12-06": (23, "Abu Dhabi Grand Prix")})
    assert list(mapa) == ["ABU DHABI"]
    assert "AVISO" in capsys.readouterr().out
