"""Pestaña Final: el podio, "Tu temporada" y cuándo se desbloquea."""

import pandas as pd
import pytest

import f1.final as final
from f1.config import COL_PUESTOS


def _df_carrera(carrera, filas):
    """filas: [(participante, puntos, primer_puesto, detalles)]"""
    datos = []
    for p, pts, primero, det in filas:
        fila = {c: "" for c in COL_PUESTOS}
        fila.update({"Participante": p, "Puntos": pts, "Primer puesto": primero,
                     "Detalles": det, "Carrera": carrera})
        datos.append(fila)
    return pd.DataFrame(datos)


FUERA = "Lance Stroll: No terminó la carrera en el top 10 (0 pts)"
EXACTO = "Max Verstappen: Exacto en P1 (+10)"


@pytest.fixture
def temporada():
    dfs = [
        _df_carrera("Australia", [("ana", 50, "Max Verstappen", f"{EXACTO}<br>{FUERA}"),
                                  ("beto", 30, "Lando Norris", FUERA),
                                  ("caro", 20, "Max Verstappen", "")]),
        _df_carrera("China", [("ana", 10, "Max Verstappen", FUERA),
                              ("beto", 40, "Lando Norris", EXACTO),
                              ("caro", 40, "Lando Norris", EXACTO)]),
        _df_carrera("Japon", [("ana", 60, "Lando Norris", EXACTO),
                              ("beto", 20, "Lando Norris", FUERA),
                              ("caro", 5, "Max Verstappen", FUERA)]),
    ]
    rankings = pd.concat([df[["Participante", "Puntos", "Carrera"]] for df in dfs])
    acumulado = (rankings.groupby("Participante", as_index=False)["Puntos"].sum()
                 .sort_values("Puntos", ascending=False).reset_index(drop=True))
    acumulado["Posición"] = acumulado.index + 1
    return acumulado, rankings, dfs


def test_ganadores_por_carrera_con_empate(temporada):
    _, rankings, _ = temporada
    g = final.ganadores_por_carrera(rankings)
    assert g["Australia"] == ["ana"]
    assert g["China"] == ["beto", "caro"]          # empate arriba: ganan los dos


def test_podio(temporada):
    acumulado, rankings, _ = temporada
    podio = final.resumen_podio(acumulado, rankings, {"ana": [{}, {}]})
    assert [p["participante"] for p in podio] == ["ana", "beto", "caro"]
    ana = podio[0]
    assert (ana["puntos"], ana["carreras_ganadas"], ana["logros"]) == (120, 2, 2)
    assert (ana["mejor_carrera"], ana["mejor_puntos"]) == ("Japon", 60)


def test_tu_temporada(temporada):
    acumulado, rankings, dfs = temporada
    t = final.tu_temporada("ana", rankings, dfs, acumulado)
    assert t["puesto"] == 1 and t["puntos"] == 120 and t["carreras"] == 3
    assert t["fetiche"] == ("Max Verstappen", 2)
    assert t["traidor"] == ("Lance Stroll", 2)
    assert t["mejor"] == ("Japon", 60) and t["peor"] == ("China", 10)
    assert t["exactos"] == 2
    # ana 2, beto 1, caro 1: promedio 4/3.
    assert t["exactos_promedio"] == pytest.approx(4 / 3, abs=0.05)


def test_nemesis_es_quien_mas_le_gano(temporada):
    acumulado, rankings, dfs = temporada
    # Contra ana, caro perdió 2 y ganó 1; contra beto perdió 2 y empató 1.
    # La némesis es la peor diferencia: beto.
    n = final.tu_temporada("caro", rankings, dfs, acumulado)["nemesis"]
    assert (n["rival"], n["gano"], n["perdio"], n["empato"]) == ("beto", 0, 2, 1)
    # ana no perdió más de lo que ganó contra nadie: no tiene némesis.
    assert final.tu_temporada("ana", rankings, dfs, acumulado)["nemesis"] is None


def test_antes_de_la_ultima_carrera_muestra_la_espera(temporada, monkeypatch):
    acumulado, rankings, dfs = temporada
    monkeypatch.setattr(final, "carreras_totales", lambda: 5)
    html = final.generar_panel_final(acumulado, rankings, dfs, {})
    assert 'data-terminada="0"' in html
    assert "Faltan <b>2</b> carreras" in html
    assert '<div class="fin-revelado" hidden>' in html


def test_con_la_ultima_carrera_se_revela_sola(temporada, monkeypatch):
    acumulado, rankings, dfs = temporada
    monkeypatch.setattr(final, "carreras_totales", lambda: 3)
    html = final.generar_panel_final(acumulado, rankings, dfs, {})
    assert 'data-terminada="1"' in html
    assert "fin-espera" not in html
    assert '<div class="fin-revelado" >' in html
    assert html.count('class="fin-tarjeta"') == 3


def test_los_nombres_se_escapan(temporada, monkeypatch):
    acumulado, rankings, dfs = temporada
    acumulado = acumulado.replace({"ana": "<b>ana</b>"})
    rankings = rankings.replace({"ana": "<b>ana</b>"})
    dfs = [d.replace({"ana": "<b>ana</b>"}) for d in dfs]
    html = final.generar_panel_final(acumulado, rankings, dfs, {})
    assert "<b>ana</b>" not in html and "&lt;b&gt;ana&lt;/b&gt;" in html
