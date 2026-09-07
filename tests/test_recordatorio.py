"""Cuándo sale y cuándo NO sale el recordatorio de votación.

El aviso tiene que salir una hora antes de cada carrera. Con el workflow
corriendo a cada hora en punto y una ventana de 110 minutos, cae exactamente
una corrida adentro por carrera: la de T-60. Estos tests fijan ese
comportamiento, porque un cambio de la ventana o del cron lo rompe en silencio
-- el aviso simplemente no llega y nadie se entera hasta que falta gente en el
ranking.
"""

import re
from datetime import datetime, timedelta, timezone

import pytest

from f1.config import CALENDARIO
from recordar_votos import VENTANA_MINUTOS, proxima_carrera

CRON_CADA_HORA = timedelta(hours=1)


def carreras_del_torneo():
    for entrada in CALENDARIO:
        iso = entrada.get("FechaISO")
        if iso:
            yield re.sub(r"<[^>]+>", "", entrada["Carrera"]).strip(), datetime.fromisoformat(iso)


def corridas_en_ventana(largada):
    """Corridas horarias que caen dentro de la ventana, antes de la largada."""
    slots, t = [], largada.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    while True:
        falta = (largada - t).total_seconds() / 60
        if falta > VENTANA_MINUTOS:
            return slots
        if falta > 0:
            slots.append(falta)
        t -= CRON_CADA_HORA


@pytest.mark.parametrize("nombre, largada", list(carreras_del_torneo()),
                         ids=lambda x: x if isinstance(x, str) else "")
def test_cada_carrera_recibe_un_aviso_una_hora_antes(nombre, largada):
    slots = corridas_en_ventana(largada)
    assert slots, f"{nombre} se quedaría sin recordatorio"
    assert max(slots) == 60, (
        f"{nombre}: el primer aviso saldría {max(slots):.0f} min antes, no 60")


def test_la_ventana_deja_pasar_una_sola_corrida():
    # Si entraran dos, la primera dispararía dos horas antes en vez de una.
    # Si no entrara ninguna, no habría aviso.
    for nombre, largada in carreras_del_torneo():
        assert len(corridas_en_ventana(largada)) == 1, nombre


def test_la_ventana_tolera_atrasos_de_github():
    # Los cron de GitHub llegan tarde. Un atraso de hasta una hora sobre la
    # corrida de T-60 igual cae adentro de la ventana y el aviso sale.
    assert VENTANA_MINUTOS >= 60, "sin margen para un atraso del cron"


def test_no_se_avisa_de_una_carrera_que_ya_largo(monkeypatch, capsys, tmp_path):
    import recordar_votos as rv
    from f1 import avisos

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(avisos, "CARPETA", tmp_path / "avisos")
    monkeypatch.setattr(avisos, "ESTADO", tmp_path / "estado.json")
    # una carrera que largó hace cinco minutos
    monkeypatch.setattr(rv, "proxima_carrera",
                        lambda ahora=None: ("ITALIA",
                                            datetime.now(timezone.utc) - timedelta(minutes=5)))
    rv.main()

    assert "ya largó" in capsys.readouterr().out
    assert not (tmp_path / "avisos").exists(), "mandó un aviso de una votación cerrada"


def test_no_se_avisa_si_falta_mucho(monkeypatch, capsys, tmp_path):
    import recordar_votos as rv
    from f1 import avisos

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(avisos, "CARPETA", tmp_path / "avisos")
    monkeypatch.setattr(rv, "proxima_carrera",
                        lambda ahora=None: ("MADRID",
                                            datetime.now(timezone.utc) + timedelta(days=3)))
    rv.main()

    assert "falta mucho" in capsys.readouterr().out
    assert not (tmp_path / "avisos").exists()
