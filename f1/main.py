# -*- coding: utf-8 -*-
"""Punto de entrada: orquesta el pipeline completo y escribe el HTML."""

import json
import os
import re

import pandas as pd

from .badges import calcular_badges
from .charts import generar_grafico_barras_acumulado
from .config import ARCHIVO_RESULTADOS, CALENDARIO, CARPETA_RESPUESTAS
from .normalizacion import normalizar_nombre_carrera, normalizar_resultados_api
from .perfiles import (
    generar_estadisticas_adicionales,
    generar_hof_panel_html,
    generar_perfil_selector_html,
    generar_perfiles_html,
)
from .render import generar_html
from .scoring import calcular_cambios_posiciones, procesar_carrera
from .validacion import validar_resultados


ARCHIVO_SALIDA_HTML = "ranking_f1.html"


def main():
    if not os.path.exists(CARPETA_RESPUESTAS):
        print(f"Carpeta '{CARPETA_RESPUESTAS}' no existe. Créala y agregá los CSV.")
        return

    if not os.path.exists(ARCHIVO_RESULTADOS):
        print(f"ERROR: No se encontró '{ARCHIVO_RESULTADOS}'. Creá el archivo con los resultados de cada carrera.")
        return

    with open(ARCHIVO_RESULTADOS, 'r', encoding='utf-8') as f:
        try:
            resultados_por_carrera = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: '{ARCHIVO_RESULTADOS}' no es un JSON válido.\n  Detalle: {e}")
            return

    # 🔧 Normalizar nombres de pilotos que vienen de la API con otra grafía
    # (con/sin tildes, "Oliver" vs "Ollie", "Alexander" vs "Alex", etc.)
    resultados_por_carrera = normalizar_resultados_api(resultados_por_carrera)

    if not validar_resultados(resultados_por_carrera):
        return

    rankings_por_carrera = []
    all_rankings = pd.DataFrame()
    all_dfs = []

    orden_calendario = [
        normalizar_nombre_carrera(
            re.sub(r'<[^>]+>', '', entry["Carrera"]).strip()
        )
        for entry in CALENDARIO
        if "<s>" not in entry["Carrera"]
    ]

    csv_por_carrera = {}
    for archivo in os.listdir(CARPETA_RESPUESTAS):
        if archivo.endswith(".csv"):
            nombre_raw = archivo.replace("respuestas_", "").replace(".csv", "")
            nombre_norm = normalizar_nombre_carrera(nombre_raw)
            csv_por_carrera[nombre_norm] = archivo

    archivos_ordenados = []
    for nombre in orden_calendario:
        if nombre in csv_por_carrera:
            archivos_ordenados.append(csv_por_carrera[nombre])

    for nombre, archivo in list(csv_por_carrera.items()):
        if archivo not in archivos_ordenados:
            archivos_ordenados.append(archivo)

    for archivo in archivos_ordenados:
        nombre_raw = archivo.replace("respuestas_", "").replace(".csv", "")
        nombre_carrera = normalizar_nombre_carrera(nombre_raw)
        datos = resultados_por_carrera.get(nombre_carrera, {})

        if datos.get("resultado_carrera"):
            archivo_path = os.path.join(CARPETA_RESPUESTAS, archivo)
            ranking, df = procesar_carrera(nombre_carrera, archivo_path, datos)
            rankings_por_carrera.append(ranking)
            all_rankings = pd.concat([all_rankings, ranking.drop(columns=["Detalles"])])
            all_dfs.append(df)
        else:
            print(f"Advertencia: [{nombre_carrera}] sin resultados todavía, se omite.")

    if not all_rankings.empty:
        ranking_acumulado = (
            all_rankings.groupby("Participante", as_index=False)["Puntos"]
            .sum().sort_values("Puntos", ascending=False).reset_index(drop=True)
        )
        ranking_acumulado["Posición"] = ranking_acumulado.index + 1
        ranking_acumulado = ranking_acumulado[["Posición", "Participante", "Puntos"]]
        ranking_acumulado = calcular_cambios_posiciones(all_rankings, ranking_acumulado)
    else:
        ranking_acumulado = pd.DataFrame(columns=["Posición", "Participante", "Puntos", "Cambio"])

    badges_por_participante = calcular_badges(all_rankings, all_dfs, ranking_acumulado)

    grafico_barras         = generar_grafico_barras_acumulado(ranking_acumulado)
    stats_adicionales      = generar_estadisticas_adicionales(all_dfs, ranking_acumulado)
    perfiles_html          = generar_perfiles_html(all_rankings, all_dfs, ranking_acumulado, badges_por_participante)
    perfil_selector_html   = generar_perfil_selector_html(ranking_acumulado)
    hof_panel_html         = generar_hof_panel_html()

    html_content = generar_html(
        rankings_por_carrera, ranking_acumulado,
        grafico_barras,
        stats_adicionales, perfiles_html,
        badges_por_participante,
        perfil_selector_html=perfil_selector_html,
        hof_panel_html=hof_panel_html,
    )

    with open(ARCHIVO_SALIDA_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"🏁 HTML generado: {ARCHIVO_SALIDA_HTML}")
    print("   Abrilo en cualquier navegador o celular.")
