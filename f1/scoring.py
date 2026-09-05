# -*- coding: utf-8 -*-
"""Puntos por carrera y armado del ranking acumulado."""

import numpy as np
import pandas as pd
from typing import Dict, Tuple

from .calendario import carreras_en_orden
from .config import COL_PUESTOS
from .participantes import COLUMNA_PARTICIPANTE, nombre_participante


def puntos_posicion(predicha: int, real: int) -> int:
    """Puntos por un piloto, segun donde lo pusiste y donde termino.

    Es la regla del torneo escrita en un solo lugar:
      - clavarla exacta ............ 10
      - errarle por un puesto ......  5  (vale aunque el real haya sido P11)
      - solo acertar que entraba ...  1
      - el resto ...................  0

    Antes esta funcion existia pero no la llamaba nadie, y ademas devolvia 1
    donde el calculo real da 0: cualquiera que la leyera para entender el
    puntaje se llevaba una idea equivocada.
    """
    if predicha == real:
        return 10
    if abs(predicha - real) == 1:
        return 5
    if real <= 10:
        return 1
    return 0


def calcular_puntos_y_detalles(row, posiciones_reales: Dict, vuelta_rapida_real: str, colapinto_real: int):
    puntos = 0
    detalles = []

    for i, col in enumerate(COL_PUESTOS, 1):
        piloto = str(row.get(col, "")).strip()
        if not piloto:
            continue

        posicion_predicha = i
        posicion_real = posiciones_reales.get(piloto)

        if posicion_real is None:
            # Piloto no terminó la carrera (no está en los resultados) → 0 puntos
            detalles.append(f"{piloto}: No terminó la carrera en el top 10 (0 pts)")
            continue

        # Ojo con el orden: la diferencia de 1 se evalua ANTES de descartar por
        # "fuera del top 10 real". Un predicho P10 que termina P11 sigue siendo
        # diferencia de 1 y suma 5, aunque el real quede un puesto afuera.
        ganados = puntos_posicion(posicion_predicha, posicion_real)
        puntos += ganados

        if ganados == 10:
            detalles.append(f"{piloto}: Exacto en P{posicion_predicha} (+10)")
        elif ganados == 5:
            detalles.append(f"{piloto}: Diff 1 (pred P{posicion_predicha}, real P{posicion_real}) (+5)")
        elif ganados == 1:
            detalles.append(f"{piloto}: En top 10 (pred P{posicion_predicha}, real P{posicion_real}) (+1)")
        else:
            detalles.append(f"{piloto}: Fuera del top 10 real (pred P{posicion_predicha}, real P{posicion_real}) (0 pts)")

    # Vuelta Rápida
    vr = str(row.get("Vuelta Rápida", "")).strip()
    if vr and vr == vuelta_rapida_real:
        puntos += 10
        detalles.append(f"Vuelta rápida: {vr} (+10)")

    # Colapinto
    try:
        pred_colapinto_str = str(row.get("Franco Colapinto", "")).strip()
        pred_colapinto = convertir_posicion_a_numero(pred_colapinto_str)
        if pred_colapinto == colapinto_real:
            puntos += 10
            detalles.append(f"Colapinto: EXACTO (+10)")
        elif abs(pred_colapinto - colapinto_real) == 1 and colapinto_real != 0:
            puntos += 5
            detalles.append(f"Colapinto: diferencia de 1 (+5)")
    except (ValueError, TypeError):
        # No cargó la predicción de Colapinto, o la escribió de una forma que
        # no sabemos leer: no suma nada. Se atrapa solo eso a propósito; un
        # `except:` pelado tapaba tambien errores de programación nuestros.
        pass

    detalle_str = "<br>".join(detalles) if detalles else "Sin puntos"
    return puntos, detalle_str


def convertir_posicion_a_numero(pos_str: str) -> int:
    mapa = {
        "Primero": 1, "Segundo": 2, "Tercer": 3, "Cuarto": 4, "Quinto": 5,
        "Sexto": 6, "Séptimo": 7, "Septimo": 7, "Octavo": 8, "Noveno": 9,
        "Décimo": 10, "Decimo": 10, "Undécimo": 11, "Duodécimo": 12,
        "Décimo Primer": 11, "Décimo Primero": 11,
        "Décimo Segundo": 12, "Décimo Tercer": 13, "Décimo Tercero": 13,
        "Décimo Cuarto": 14, "Décimo Quinto": 15, "Décimo Sexto": 16,
        "Décimo Séptimo": 17, "Décimo Octavo": 18, "Décimo Noveno": 19, "Vigésimo": 20,
    }
    pos_str_lower = pos_str.lower().replace("puesto", "").strip()
    # Probar primero las frases más largas para que "Décimo Segundo" no
    # matchee por error con "Segundo" o "Décimo" sueltos.
    for key in sorted(mapa, key=len, reverse=True):
        if key.lower() in pos_str_lower:
            return mapa[key]
    return int(pos_str)


def procesar_carrera(nombre_carrera: str, archivo_csv: str, resultados: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(archivo_csv)
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
    # Traduccion a apodo apenas entra el dato: de aca para adelante ningun
    # mail viaja hacia el HTML publicado (ver f1/participantes.py).
    df[COLUMNA_PARTICIPANTE] = df[COLUMNA_PARTICIPANTE].map(nombre_participante)
    resultado_carrera = resultados.get("resultado_carrera", [])
    vuelta_rapida_real = resultados.get("vuelta_rapida", "")
    colapinto_real = resultados.get("colapinto", 0)
    if isinstance(colapinto_real, str):
        try:
            colapinto_real = convertir_posicion_a_numero(colapinto_real)
        except (ValueError, TypeError):
            colapinto_real = 0
    posiciones_reales = {piloto: i+1 for i, piloto in enumerate(resultado_carrera)}
    df[["Puntos", "Detalles"]] = df.apply(
        lambda row: pd.Series(calcular_puntos_y_detalles(
            row, posiciones_reales, vuelta_rapida_real, colapinto_real)),
        axis=1
    )
    df["Carrera"] = nombre_carrera
    ranking = df.groupby("Participante", as_index=False).agg({
        "Puntos": "sum",
        "Detalles": lambda x: "<br><br>".join(x)
    }).sort_values("Puntos", ascending=False).reset_index(drop=True)
    ranking["Posición"] = ranking.index + 1
    ranking = ranking[["Posición", "Participante", "Puntos", "Detalles"]]
    ranking["Carrera"] = nombre_carrera
    return ranking, df


def calcular_cambios_posiciones(all_rankings: pd.DataFrame, ranking_acumulado: pd.DataFrame) -> pd.DataFrame:
    if len(all_rankings['Carrera'].unique()) < 2:
        ranking_acumulado['Cambio'] = '-'
        return ranking_acumulado
    carreras = carreras_en_orden(all_rankings['Carrera'].unique().tolist())
    prev_rankings = all_rankings[all_rankings['Carrera'] != carreras[-1]]
    if prev_rankings.empty:
        acum_prev = pd.Series()
    else:
        acum_prev = prev_rankings.groupby("Participante")["Puntos"].sum()\
            .sort_values(ascending=False).reset_index()
        acum_prev["Posición"] = acum_prev.index + 1
        acum_prev = acum_prev.set_index('Participante')['Posición']
    cambios = {}
    for participante in ranking_acumulado['Participante']:
        pos_actual = ranking_acumulado[
            ranking_acumulado['Participante'] == participante]['Posición'].values[0]
        pos_prev = acum_prev.get(participante, None)
        if pos_prev is None or not np.isfinite(pos_prev):
            cambios[participante] = '<span class="trend-neutral">—</span>'
            continue
        diff = pos_prev - pos_actual
        if diff > 0:
            cambios[participante] = f'<span class="trend-up">▲{int(diff)}</span>'
        elif diff < 0:
            cambios[participante] = f'<span class="trend-down">▼{int(-diff)}</span>'
        else:
            cambios[participante] = '<span class="trend-neutral">—</span>'
    ranking_acumulado['Cambio'] = ranking_acumulado['Participante'].map(cambios)
    return ranking_acumulado


def calcular_historial_posiciones(all_rankings: pd.DataFrame) -> pd.DataFrame:
    if all_rankings.empty:
        return pd.DataFrame()
    carreras = carreras_en_orden(all_rankings['Carrera'].unique().tolist())
    rows = []
    for i, carrera in enumerate(carreras):
        subset = all_rankings[all_rankings['Carrera'].isin(carreras[:i+1])]
        acum = subset.groupby("Participante")["Puntos"].sum()\
            .sort_values(ascending=False).reset_index()
        acum["Posición"] = acum.index + 1
        acum["Carrera"] = carrera
        rows.append(acum)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
