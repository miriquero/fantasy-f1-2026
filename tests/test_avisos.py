"""Los tres avisos automáticos.

Todos comparten el mismo riesgo: o no avisan cuando deberían, o avisan de lo
mismo dos veces por día para siempre. Los dos casos se testean acá.
"""

from datetime import datetime, timedelta, timezone

import pytest

import fetch_resultados
import fetch_votos
import recordar_votos
from f1 import avisos


@pytest.fixture(autouse=True)
def _carpeta_limpia(tmp_path, monkeypatch):
    """Cada test escribe en su propio directorio, no en el del repo."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(avisos, "CARPETA", tmp_path / "avisos")
    monkeypatch.setattr(avisos, "ESTADO", tmp_path / "estado_avisos.json")


# --------------------------------------------------------------- mecanismo
def test_un_aviso_queda_donde_el_workflow_lo_busca():
    avisos.anotar("penalidad", "cambió Hungría")
    assert (avisos.CARPETA / "penalidad.txt").read_text(encoding="utf-8").strip() == "cambió Hungría"


def test_un_aviso_vacio_no_crea_archivo():
    # El workflow decide con `[ -s archivo ]`. Un archivo vacío mandaría un
    # WhatsApp en blanco.
    avisos.anotar("penalidad", "   ")
    assert not (avisos.CARPETA / "penalidad.txt").exists()


def test_el_estado_recuerda_entre_corridas():
    estado = avisos.leer_estado()
    assert avisos.ya_avisado(estado, "tardios", "x") is False
    avisos.marcar_avisado(estado, "tardios", "x")
    avisos.guardar_estado(estado)
    assert avisos.ya_avisado(avisos.leer_estado(), "tardios", "x") is True


def test_un_estado_corrupto_no_frena_el_pipeline():
    avisos.ESTADO.write_text("{ esto no es json", encoding="utf-8")
    assert avisos.leer_estado() == {}


# ------------------------------------------------------- aviso de penalidad
def test_describe_en_que_posicion_cambio_el_resultado():
    antes = ["Verstappen", "Norris", "Leclerc"]
    ahora = ["Norris", "Verstappen", "Leclerc"]
    assert fetch_resultados.describir_correccion(antes, ahora) == "P1: Verstappen → Norris"


def test_si_no_cambio_nada_no_inventa_una_diferencia():
    iguales = ["Verstappen", "Norris"]
    assert "cambió" in fetch_resultados.describir_correccion(iguales, iguales)


# ---------------------------------------------------------- voto tardío
@pytest.mark.parametrize("minutos, esperado", [
    (1, "1 minuto"), (14, "14 minutos"), (60, "1 hora"),
    (200, "3 horas"), (60 * 24, "1 día"), (60 * 24 * 3, "3 días"),
])
def test_el_atraso_se_escribe_como_lo_diria_una_persona(minutos, esperado):
    assert fetch_votos._atraso_legible(minutos) == esperado


# ---------------------------------------------------------- recordatorio
def test_la_proxima_carrera_es_la_siguiente_del_calendario():
    # A mitad de temporada, mirando desde justo después de Italia.
    despues_de_italia = datetime(2026, 9, 7, tzinfo=timezone.utc)
    nombre, largada = recordar_votos.proxima_carrera(despues_de_italia)
    assert nombre == "MADRID"
    assert largada > despues_de_italia


def test_terminada_la_temporada_no_hay_proxima():
    nombre, largada = recordar_votos.proxima_carrera(
        datetime(2027, 1, 1, tzinfo=timezone.utc))
    assert (nombre, largada) == (None, None)


def test_las_carreras_tachadas_no_cuentan_como_proximas():
    # Bahréin y Arabia Saudita están tachadas del torneo: nunca deberían
    # disparar un recordatorio.
    antes_de_bahrein = datetime(2026, 4, 1, tzinfo=timezone.utc)
    nombre, _ = recordar_votos.proxima_carrera(antes_de_bahrein)
    assert nombre == "MIAMI"
