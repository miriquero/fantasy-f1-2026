import pandas as pd

from f1.badges import calcular_badges

EMAIL_COL = "Participante"

CARRERAS = ["Carrera 1", "Carrera 2", "Carrera 3", "Carrera 4", "Carrera 5"]


def _armar_datos():
    """Participante A acierta P1 exacto en las 5 carreras y termina 1° del
    ranking general; participante B nunca acierta y termina 2°."""
    filas_rankings = []
    dfs = []
    for carrera in CARRERAS:
        ranking = pd.DataFrame({
            "Posición": [1, 2],
            EMAIL_COL: ["a@example.com", "b@example.com"],
            "Puntos": [10, 1],
            "Carrera": [carrera, carrera],
        })
        filas_rankings.append(ranking)

        df = pd.DataFrame({
            EMAIL_COL: ["a@example.com", "b@example.com"],
            "Puntos": [10, 1],
            "Detalles": ["Max Verstappen: Exacto en P1 (+10)", "Max Verstappen: En top 10 (pred P1, real P3) (+1)"],
            "Carrera": [carrera, carrera],
        })
        dfs.append(df)

    all_rankings = pd.concat(filas_rankings, ignore_index=True)
    ranking_acumulado = pd.DataFrame({
        "Posición": [1, 2],
        EMAIL_COL: ["a@example.com", "b@example.com"],
        "Puntos": [50, 5],
    })
    return all_rankings, dfs, ranking_acumulado


def test_calcular_badges_francotirador_y_rey_temporada():
    all_rankings, dfs, ranking_acumulado = _armar_datos()
    badges = calcular_badges(all_rankings, dfs, ranking_acumulado)

    nombres_a = {b["nombre"] for b in badges["a@example.com"]}
    assert "Francotirador" in nombres_a  # 5+ aciertos exactos de P1
    assert "Rey de la Temporada" in nombres_a  # 1° del ranking general

    nombres_b = {b["nombre"] for b in badges["b@example.com"]}
    assert "Francotirador" not in nombres_b
    assert "Rey de la Temporada" not in nombres_b


def test_calcular_badges_sin_datos_devuelve_vacio():
    vacio = pd.DataFrame()
    assert calcular_badges(vacio, [], vacio) == {}
