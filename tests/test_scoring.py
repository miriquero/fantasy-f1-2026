import pandas as pd

from f1.scoring import calcular_puntos_y_detalles, convertir_posicion_a_numero, puntos_posicion


def test_puntos_posicion_exacto():
    assert puntos_posicion(1, 1) == 10


def test_puntos_posicion_diferencia_uno():
    assert puntos_posicion(2, 1) == 5
    assert puntos_posicion(1, 2) == 5


def test_puntos_posicion_otro_valor():
    assert puntos_posicion(1, 5) == 1


def test_convertir_posicion_a_numero_texto():
    assert convertir_posicion_a_numero("Primero") == 1
    assert convertir_posicion_a_numero("Décimo Quinto Puesto") == 15
    assert convertir_posicion_a_numero("Vigésimo") == 20


def test_convertir_posicion_a_numero_numerico():
    assert convertir_posicion_a_numero("14") == 14


def _fila(**kwargs):
    base = {
        "Primer puesto": "", "Segundo puesto": "", "Tercer puesto": "",
        "Cuarto puesto": "", "Quinto puesto": "", "Sexto puesto": "",
        "Séptimo puesto": "", "Octavo puesto": "", "Noveno puesto": "",
        "Décimo puesto": "", "Vuelta Rápida": "", "Franco Colapinto": "",
    }
    base.update(kwargs)
    return pd.Series(base)


def test_calcular_puntos_acierto_exacto_y_vuelta_rapida():
    posiciones_reales = {"Max Verstappen": 1}
    row = _fila(**{"Primer puesto": "Max Verstappen", "Vuelta Rápida": "Max Verstappen"})
    puntos, detalle = calcular_puntos_y_detalles(row, posiciones_reales, "Max Verstappen", 0)
    assert puntos == 20  # 10 por P1 exacto + 10 por vuelta rápida
    assert "Exacto en P1" in detalle
    assert "Vuelta rápida" in detalle


def test_calcular_puntos_piloto_que_no_figura_en_los_resultados():
    # El piloto predicho no aparece en el resultado de la carrera (abandono, o
    # quedó fuera del top 11 que guardamos). Esa es una rama distinta de la de
    # "figura pero afuera del top 10", que cubre el test de más abajo.
    posiciones_reales = {}
    row = _fila(**{"Primer puesto": "Yuki Tsunoda"})
    puntos, detalle = calcular_puntos_y_detalles(row, posiciones_reales, "", 0)
    assert puntos == 0
    assert "No terminó la carrera en el top 10" in detalle


def test_calcular_puntos_colapinto_exacto():
    row = _fila(**{"Franco Colapinto": "Décimo Puesto"})
    puntos, detalle = calcular_puntos_y_detalles(row, {}, "", 10)
    assert puntos == 10
    assert "Colapinto: EXACTO" in detalle


def test_calcular_puntos_p10_predicho_p11_real_es_diferencia_de_uno():
    # Si predije a un piloto en el P10 y terminó P11, cuenta como "diferencia
    # de uno" (5 pts), no como "fuera del top 10" (0 pts).
    posiciones_reales = {"Esteban Ocon": 11}
    row = _fila(**{"Décimo puesto": "Esteban Ocon"})
    puntos, detalle = calcular_puntos_y_detalles(row, posiciones_reales, "", 0)
    assert puntos == 5
    assert "Diff 1 (pred P10, real P11)" in detalle


def test_calcular_puntos_p11_real_sin_prediccion_p10_no_suma():
    # Si el piloto termina P11 pero se lo predijo en un puesto que no es P10
    # (ni P12, que no existe como predicción posible), no debe sumar el punto
    # de consuelo de "top 10" — P11 no es top 10.
    posiciones_reales = {"Esteban Ocon": 11}
    row = _fila(**{"Octavo puesto": "Esteban Ocon"})
    puntos, detalle = calcular_puntos_y_detalles(row, posiciones_reales, "", 0)
    assert puntos == 0
    assert "Fuera del top 10 real" in detalle
