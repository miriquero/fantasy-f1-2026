"""Cuándo sale y cuándo NO sale el recordatorio de votación.

El diseño de dos ventanas no es un capricho: GitHub no ejecuta los cron como
uno espera. Con `cron: 0 * * * *` se midieron 5,6 corridas por día de 24 (el
23%), con huecos de 4,1 h de mediana y hasta 10,6 h. Con una sola ventana de
110 minutos el recordatorio de Madrid nunca salió — entre las 03:28 y las
14:05 de ese día no corrió nada y la carrera era a las 13:00.

De ahí las dos ventanas: la ancha asegura la entrega, la urgente es un extra.
Estos tests fijan que la ancha siga siendo más grande que el peor hueco
observado, porque si alguien la achica el aviso vuelve a no llegar y nadie se
entera hasta que falta gente en el ranking.
"""

import re
from datetime import datetime, timedelta, timezone

import pytest

from f1.config import CALENDARIO
from recordar_votos import VENTANA_ANCHA, VENTANA_ULTIMA, cuanto_falta, proxima_carrera

# Medido sobre 107 corridas reales del workflow, del 13 al 24 de septiembre.
PEOR_HUECO_OBSERVADO_MIN = 10.6 * 60


def carreras_del_torneo():
    for entrada in CALENDARIO:
        iso = entrada.get("FechaISO")
        if iso:
            yield re.sub(r"<[^>]+>", "", entrada["Carrera"]).strip(), datetime.fromisoformat(iso)


# ------------------------------------------------------------------- ventanas
def test_la_ventana_ancha_supera_el_peor_hueco_medido():
    # Si no lo supera, hay carreras para las que no va a correr nada adentro
    # de la ventana y el aviso simplemente no sale.
    assert VENTANA_ANCHA > PEOR_HUECO_OBSERVADO_MIN, (
        f"con {VENTANA_ANCHA} min una racha de {PEOR_HUECO_OBSERVADO_MIN:.0f} min "
        f"sin corridas deja la carrera sin aviso")


def test_la_urgente_es_mas_chica_que_la_ancha():
    assert VENTANA_ULTIMA < VENTANA_ANCHA


def test_la_ventana_ancha_no_avisa_con_dias_de_anticipacion():
    # Avisar tres días antes no sirve: se olvidan igual.
    assert VENTANA_ANCHA <= 24 * 60


@pytest.mark.parametrize("nombre, largada", list(carreras_del_torneo()),
                         ids=lambda x: x if isinstance(x, str) else "")
def test_toda_carrera_tiene_margen_para_el_aviso_ancho(nombre, largada):
    # La ventana empieza el día anterior: siempre hay tiempo real para votar.
    assert VENTANA_ANCHA >= 60, nombre


# ------------------------------------------------------------------- redacción
@pytest.mark.parametrize("minutos, esperado", [
    (1, "1 minuto"), (47, "47 minutos"), (89, "89 minutos"),
    (90, "2 horas"), (180, "3 horas"), (60 * 20, "20 horas"),
    (60 * 25, "1 día"),
])
def test_el_tiempo_restante_se_escribe_como_lo_diria_una_persona(minutos, esperado):
    assert cuanto_falta(minutos) == esperado


# ------------------------------------------------------------------- calendario
def test_la_proxima_carrera_es_la_siguiente_del_calendario():
    despues_de_italia = datetime(2026, 9, 7, tzinfo=timezone.utc)
    nombre, largada = proxima_carrera(despues_de_italia)
    assert nombre == "MADRID"
    assert largada > despues_de_italia


def test_bahrein_entra_entre_azerbaiyan_y_singapur():
    # Bahréin no se canceló: se mudó a Malasia y corre el 4 de octubre.
    nombre, largada = proxima_carrera(datetime(2026, 9, 27, tzinfo=timezone.utc))
    assert nombre == "BAHRÉIN"
    assert largada.date().isoformat() == "2026-10-04"

    siguiente, _ = proxima_carrera(datetime(2026, 10, 5, tzinfo=timezone.utc))
    assert siguiente == "SINGAPUR"


def test_terminada_la_temporada_no_hay_proxima():
    assert proxima_carrera(datetime(2027, 1, 1, tzinfo=timezone.utc)) == (None, None)


def test_las_carreras_canceladas_no_disparan_recordatorios():
    # Arabia Saudita sí está cancelada de verdad y no debe aparecer nunca.
    nombres = {n for n, _ in carreras_del_torneo()}
    assert "ARABIA SAUDITA" not in nombres
    assert "BAHRÉIN" in nombres


# ------------------------------------------------------------------- decisiones
def _corre(monkeypatch, tmp_path, faltan, estado_previo=None):
    import recordar_votos as rv
    from f1 import avisos

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(avisos, "CARPETA", tmp_path / "avisos")
    monkeypatch.setattr(avisos, "ESTADO", tmp_path / "estado.json")
    if estado_previo is not None:
        avisos.guardar_estado(estado_previo)
    monkeypatch.setattr(rv, "proxima_carrera",
                        lambda ahora=None: ("MADRID", datetime.now(timezone.utc) + faltan))
    monkeypatch.setattr(rv, "plantel", lambda: {"ana", "beto"})
    monkeypatch.setattr(rv, "ya_votaron", lambda c: {"ana"})
    rv.main()
    return tmp_path / "avisos"


def test_a_quince_horas_sale_el_aviso_ancho(monkeypatch, tmp_path):
    carpeta = _corre(monkeypatch, tmp_path, timedelta(hours=15))
    assert (carpeta / "recordatorio.txt").exists()
    assert not (carpeta / "ultima_hora.txt").exists()
    assert "beto" in (carpeta / "recordatorio.txt").read_text(encoding="utf-8")


def test_a_una_hora_sale_el_urgente(monkeypatch, tmp_path):
    carpeta = _corre(monkeypatch, tmp_path, timedelta(minutes=60))
    assert (carpeta / "ultima_hora.txt").exists()
    assert not (carpeta / "recordatorio.txt").exists()


def test_el_urgente_sale_aunque_el_ancho_ya_haya_salido(monkeypatch, tmp_path):
    # Es el caso bueno: aviso el día anterior y recordatorio urgente al final.
    carpeta = _corre(monkeypatch, tmp_path, timedelta(minutes=60),
                     estado_previo={"recordatorios": ["MADRID"]})
    assert (carpeta / "ultima_hora.txt").exists()


def test_el_ancho_no_se_repite(monkeypatch, tmp_path):
    carpeta = _corre(monkeypatch, tmp_path, timedelta(hours=15),
                     estado_previo={"recordatorios": ["MADRID"]})
    assert not carpeta.exists() or not (carpeta / "recordatorio.txt").exists()


def test_no_se_avisa_de_una_carrera_que_ya_largo(monkeypatch, tmp_path):
    carpeta = _corre(monkeypatch, tmp_path, timedelta(minutes=-5))
    assert not carpeta.exists()


def test_no_se_avisa_si_falta_mucho(monkeypatch, tmp_path):
    carpeta = _corre(monkeypatch, tmp_path, timedelta(days=3))
    assert not carpeta.exists()


def test_si_votaron_todos_no_se_manda_nada(monkeypatch, tmp_path):
    import recordar_votos as rv
    from f1 import avisos

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(avisos, "CARPETA", tmp_path / "avisos")
    monkeypatch.setattr(avisos, "ESTADO", tmp_path / "estado.json")
    monkeypatch.setattr(rv, "proxima_carrera",
                        lambda ahora=None: ("MADRID",
                                            datetime.now(timezone.utc) + timedelta(hours=10)))
    monkeypatch.setattr(rv, "plantel", lambda: {"ana"})
    monkeypatch.setattr(rv, "ya_votaron", lambda c: {"ana"})
    rv.main()
    assert not (tmp_path / "avisos").exists()
