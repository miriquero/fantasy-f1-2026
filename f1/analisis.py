# -*- coding: utf-8 -*-
"""Analisis de la temporada: proyeccion al titulo y cara a cara.

Son las dos preguntas que la pagina no contestaba y que en un campeonato son
las que mas se hacen: "¿todavia llego?" y "¿a quien le gano yo?".

El resto de las estadisticas ya estaban cubiertas: los logros premian rachas y
remontadas, y el panel de perfiles muestra el rendimiento individual. Aca no se
repite nada de eso.
"""

from typing import Dict, List

import pandas as pd

from .calendario import carreras_en_orden
from .config import CALENDARIO
from .paleta import color_participante, hex_a_rgba

# Techo de puntos de una carrera: 10 aciertos exactos del top 10 (10 pts cada
# uno) + la vuelta rapida (10) + Colapinto exacto (10). Sale de las reglas de
# f1/scoring.py; si cambia el puntaje, hay que cambiar esto.
MAXIMO_POR_CARRERA = 10 * 10 + 10 + 10


def carreras_totales() -> int:
    """Cuantas carreras tiene el torneo (sin las tachadas del calendario)."""
    return sum(1 for e in CALENDARIO if e.get("FechaISO"))


def proyeccion_titulo(ranking_acumulado: pd.DataFrame,
                      carreras_jugadas: int) -> List[Dict]:
    """Quien puede todavia salir campeon, matematicamente.

    Alguien sigue con chances si, ganando el maximo posible en todas las
    carreras que faltan, alcanza al lider actual. No es una prediccion: es una
    cuenta cerrada, y por eso se puede afirmar sin adivinar nada.
    """
    if ranking_acumulado.empty:
        return []

    restantes = max(0, carreras_totales() - carreras_jugadas)
    techo = restantes * MAXIMO_POR_CARRERA
    lider = int(ranking_acumulado["Puntos"].max())

    filas = []
    for fila in ranking_acumulado.itertuples(index=False):
        puntos = int(fila.Puntos)
        diferencia = lider - puntos
        filas.append({
            "participante": str(fila.Participante),
            "puntos": puntos,
            "diferencia": diferencia,
            "maximo_posible": puntos + techo,
            "vivo": diferencia <= techo,
            "es_lider": diferencia == 0,
        })
    return filas


def cara_a_cara(all_rankings: pd.DataFrame) -> Dict[str, List[Dict]]:
    """Para cada persona, su historial contra cada rival.

    Se compara carrera por carrera: en cada una gana quien hizo mas puntos.
    Las carreras en las que alguno de los dos no jugo no cuentan, asi que
    nadie queda penalizado por haberse sumado tarde.
    """
    if all_rankings.empty:
        return {}

    carreras = carreras_en_orden(all_rankings["Carrera"].unique().tolist())
    puntos_por_carrera = {
        carrera: dict(zip(sub["Participante"], sub["Puntos"]))
        for carrera, sub in all_rankings.groupby("Carrera")
    }

    participantes = sorted(all_rankings["Participante"].unique())
    resultado = {}
    for uno in participantes:
        rivales = []
        for otro in participantes:
            if otro == uno:
                continue
            gano = perdio = empato = 0
            for carrera in carreras:
                marcador = puntos_por_carrera.get(carrera, {})
                if uno not in marcador or otro not in marcador:
                    continue
                a, b = marcador[uno], marcador[otro]
                if a > b:
                    gano += 1
                elif a < b:
                    perdio += 1
                else:
                    empato += 1
            if gano + perdio + empato:
                rivales.append({"rival": otro, "gano": gano,
                                "perdio": perdio, "empato": empato})
        rivales.sort(key=lambda r: (-r["gano"], r["perdio"]))
        resultado[uno] = rivales
    return resultado


def generar_panel_analisis(ranking_acumulado: pd.DataFrame,
                           all_rankings: pd.DataFrame) -> str:
    """Panel con la proyeccion al titulo y el cara a cara."""
    if ranking_acumulado.empty or all_rankings.empty:
        return ""

    jugadas = len(all_rankings["Carrera"].unique())
    totales = carreras_totales()
    restantes = max(0, totales - jugadas)
    proyeccion = proyeccion_titulo(ranking_acumulado, jugadas)
    vivos = [p for p in proyeccion if p["vivo"]]

    partes = ['<div class="mas-subsection">',
              '<div class="section-label">¿Quién puede salir campeón?</div>']

    if restantes == 0:
        partes.append('<p class="empty-msg">La temporada terminó.</p>')
    else:
        partes.append(
            f'<p class="analisis-intro">Faltan <strong>{restantes}</strong> '
            f'carrera{"s" if restantes != 1 else ""} y se pueden sumar hasta '
            f'<strong>{restantes * MAXIMO_POR_CARRERA}</strong> puntos. '
            f'Con eso, <strong>{len(vivos)}</strong> de {len(proyeccion)} '
            f'siguen con chances matemáticas.</p>')

        partes.append('<ul class="proy-lista">')
        for p in proyeccion:
            color = color_participante(p["participante"])
            if p["es_lider"]:
                estado, clase = "Puntero", "proy-lider"
            elif p["vivo"]:
                estado, clase = f"a {p['diferencia']} pts", "proy-vivo"
            else:
                estado, clase = "Sin chances", "proy-fuera"
            # La barra compara el maximo alcanzable de cada uno contra el mejor
            # maximo alcanzable: muestra de un vistazo quien llega y quien no.
            tope = max(x["maximo_posible"] for x in proyeccion) or 1
            ancho = round(p["maximo_posible"] / tope * 100)
            partes.append(
                f'<li class="proy-fila {clase} reveal" style="--c:{color}">'
                f'<span class="proy-nombre">{p["participante"]}</span>'
                f'<span class="proy-barra"><span class="proy-barra-fill" '
                f'style="width:{ancho}%"></span></span>'
                f'<span class="proy-estado">{estado}</span>'
                f'</li>')
        partes.append("</ul>")
        partes.append(
            '<p class="analisis-nota">No es un pronóstico: es el máximo que '
            'cada uno puede alcanzar si acierta todo lo que queda.</p>')

    partes.append("</div>")

    # ---- Cara a cara -------------------------------------------------------
    duelos = cara_a_cara(all_rankings)
    if duelos:
        nombres = sorted(duelos)
        partes.append('<div class="mas-subsection">')
        partes.append('<div class="section-label">Cara a cara</div>')
        partes.append(
            '<p class="analisis-intro">Carrera por carrera, quién le ganó a quién.</p>')
        opciones = "".join(f'<option value="{n}">{n}</option>' for n in nombres)
        partes.append(
            '<label class="h2h-label" for="h2h-select">Elegí a alguien</label>'
            f'<select id="h2h-select" class="h2h-select" '
            f'onchange="mostrarDuelos(this.value)">{opciones}</select>')

        for nombre in nombres:
            color = color_participante(nombre)
            filas = "".join(
                f'<li class="h2h-fila">'
                f'<span class="h2h-rival">{d["rival"]}</span>'
                f'<span class="h2h-marcador">'
                f'<b class="h2h-gano">{d["gano"]}</b>'
                f'<span class="h2h-sep">·</span>'
                f'<b class="h2h-perdio">{d["perdio"]}</b>'
                + (f'<span class="h2h-sep">·</span>'
                   f'<b class="h2h-empato">{d["empato"]}</b>' if d["empato"] else "")
                + '</span></li>'
                for d in duelos[nombre])
            partes.append(
                f'<div class="h2h-panel" id="h2h-{nombres.index(nombre)}" '
                f'style="--c:{color}" data-nombre="{nombre}" hidden>'
                f'<div class="h2h-leyenda">'
                f'<span><b class="h2h-gano">ganó</b></span>'
                f'<span><b class="h2h-perdio">perdió</b></span>'
                f'<span><b class="h2h-empato">empató</b></span></div>'
                f'<ul class="h2h-lista">{filas}</ul></div>')
        partes.append("</div>")

    return "".join(partes)
