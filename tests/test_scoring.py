import pandas as pd
import pytest

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
    assert "Colapinto: Exacto en P10 (+10)" in detalle


# El que termina fuera del top 10 no paga nada, cualquiera sea la prediccion.
#
# Esta es LA regla de borde del torneo y conviene tenerla escrita: antes un
# predicho P10 que terminaba P11 cobraba 5 puntos por "errarle por uno". Ya no.
# El top 10 es el corte y abajo de ahi no hay nada, ni el punto de consuelo ni
# la diferencia de uno. Los tests que fijaban la regla anterior quedaron rojos
# una semana sin que nadie se enterara, porque los commits del bot no disparan
# CI; estos fijan la vigente.
@pytest.mark.parametrize("columna, predicho", [
    ("Décimo puesto", 10),   # el caso pegado al corte: P10 predicho, P11 real
    ("Octavo puesto", 8),
    ("Primer puesto", 1),
])
def test_el_que_termina_p11_no_paga_nada(columna, predicho):
    posiciones_reales = {"Esteban Ocon": 11}
    row = _fila(**{columna: "Esteban Ocon"})
    puntos, detalle = calcular_puntos_y_detalles(row, posiciones_reales, "", 0)
    assert puntos == 0, detalle
    assert "No terminó la carrera en el top 10" in detalle
    # y que no se cuele ninguna de las dos formas de cobrar
    assert "Diff 1" not in detalle
    assert "En top 10" not in detalle


def test_dentro_del_top_10_siempre_se_cobra_algo():
    """La contracara: adentro del corte no existe el cero. Por eso el detalle
    ya no necesita una linea de "fuera del top 10 real" para un piloto que SI
    termino adentro — esa rama era inalcanzable."""
    for predicho in range(1, 11):
        for real in range(1, 11):
            assert puntos_posicion(predicho, real) in (1, 5, 10)
