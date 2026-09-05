# -*- coding: utf-8 -*-
"""Graficos en SVG, generados en Python.

Antes esto era matplotlib: se dibujaba un PNG y se incrustaba en base64. Eran
211 KB, el 48% del peso de la pagina, y como imagen fija tenia tres problemas
que en un telefono se notan mucho:

  - no se adapta al ancho: en una pantalla angosta se achica todo junto,
    incluidos los textos, hasta volverse ilegible;
  - se ve borrosa en pantallas retina, porque es un mapa de bits a 130 dpi;
  - no se puede tocar: ni hover, ni resaltar a una persona, ni tooltip.

En SVG las tres cosas se resuelven solas. El viewBox escala el dibujo sin
perder nitidez, el CSS puede resaltar series, y el `<title>` da tooltip nativo
sin una linea de JavaScript.

Todos los graficos se dibujan pensados para un telefono primero: el viewBox
mide 360 unidades de ancho, que es el ancho util de un telefono chico, y se
estira hacia arriba en pantallas grandes.
"""

from typing import Dict, List

import pandas as pd

from .calendario import carreras_en_orden
from .paleta import EJE, GRILLA, INK_MUTED, INK_SECUNDARIO, color_participante, hex_a_rgba

ANCHO = 360.0          # unidades del viewBox: un telefono chico
RADIO_PUNTA = 3.0      # esquinas redondeadas en la punta de las barras


def _escapar(texto: str) -> str:
    """Texto seguro dentro de un SVG."""
    return (str(texto).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _barra_redondeada(x: float, y: float, ancho: float, alto: float) -> str:
    """Path de una barra horizontal con la punta redondeada.

    Solo se redondea el extremo del valor. La base queda recta y pegada al eje,
    que es lo que deja comparar longitudes de un vistazo: si se redondearan los
    dos lados, las barras cortas se verian como pastillas y perderian su origen.
    """
    r = min(RADIO_PUNTA, ancho / 2, alto / 2)
    if ancho <= r:
        return f'M {x} {y} h {ancho} v {alto} h {-ancho} Z'
    return (f'M {x} {y} h {ancho - r} a {r} {r} 0 0 1 {r} {r} '
            f'v {alto - 2 * r} a {r} {r} 0 0 1 {-r} {r} h {-(ancho - r)} Z')


def grafico_barras_acumulado(ranking_acumulado: pd.DataFrame) -> str:
    """Puntos acumulados: una barra por participante, ordenadas por puntaje.

    El nombre va escrito al lado de cada barra, asi que el color es un refuerzo
    de identidad y no la unica forma de saber quien es quien.
    """
    if ranking_acumulado.empty:
        return ""

    filas = list(ranking_acumulado.itertuples(index=False))
    maximo = max(int(f.Puntos) for f in filas) or 1

    alto_fila, gap = 26.0, 6.0
    x_barra, margen_der = 96.0, 34.0
    ancho_util = ANCHO - x_barra - margen_der
    alto = len(filas) * (alto_fila + gap) + 8

    partes = [
        f'<svg class="g-barras" viewBox="0 0 {ANCHO:.0f} {alto:.0f}" '
        f'role="img" width="100%" preserveAspectRatio="xMidYMin meet" '
        f'aria-label="Puntos acumulados por participante">'
    ]

    for i, fila in enumerate(filas):
        nombre, puntos = str(fila.Participante), int(fila.Puntos)
        color = color_participante(nombre)
        y = i * (alto_fila + gap) + 4
        ancho_barra = max(2.0, ancho_util * puntos / maximo)
        centro = y + alto_fila / 2

        partes.append(
            f'<g class="g-barra" style="--c:{color}" '
            f'transform="translate(0 0)">'
            f'<title>{_escapar(nombre)}: {puntos} puntos</title>'
            f'<text class="g-nombre" x="{x_barra - 10:.0f}" y="{centro:.1f}" '
            f'text-anchor="end" dominant-baseline="central">{_escapar(nombre)}</text>'
            f'<path class="g-fondo" d="'
            f'{_barra_redondeada(x_barra, y, ancho_util, alto_fila)}"/>'
            f'<path class="g-valor" d="'
            f'{_barra_redondeada(x_barra, y, ancho_barra, alto_fila)}" '
            f'style="--w:{ancho_barra:.1f}px"/>'
            f'<text class="g-valor-num" x="{x_barra + ancho_barra + 8:.1f}" '
            f'y="{centro:.1f}" dominant-baseline="central">{puntos}</text>'
            f'</g>'
        )
    partes.append("</svg>")
    return "".join(partes)


def grafico_evolucion(all_rankings: pd.DataFrame, historial: pd.DataFrame) -> str:
    """Como se movio cada uno en la tabla, carrera a carrera.

    Es el grafico que faltaba: el de barras dice como esta hoy el campeonato,
    este dice como se llego hasta aca. Se dibujan todas las lineas en gris y
    solo se resalta la que se toca, porque diez lineas de colores distintos no
    se distinguen (ver f1/paleta.py); el color aparece al resaltar una.
    """
    if historial.empty:
        return ""

    carreras = carreras_en_orden(historial["Carrera"].unique().tolist())
    if len(carreras) < 2:
        return ""

    participantes = sorted(historial["Participante"].unique())
    n_pos = len(participantes)

    margen_izq, margen_der, margen_sup, margen_inf = 26.0, 14.0, 14.0, 30.0
    ancho_util = ANCHO - margen_izq - margen_der
    alto_util = max(120.0, n_pos * 16.0)
    alto = alto_util + margen_sup + margen_inf

    def px(i):
        return margen_izq + (ancho_util * i / max(1, len(carreras) - 1))

    def py(pos):
        return margen_sup + (alto_util * (pos - 1) / max(1, n_pos - 1))

    partes = [
        f'<svg class="g-evolucion" viewBox="0 0 {ANCHO:.0f} {alto:.0f}" '
        f'role="img" width="100%" preserveAspectRatio="xMidYMin meet" '
        f'aria-label="Evolución de las posiciones carrera a carrera">'
    ]

    # Grilla: una linea por posicion, bien tenue. Es referencia, no protagonista.
    for pos in range(1, n_pos + 1):
        y = py(pos)
        partes.append(
            f'<line class="g-grilla" x1="{margen_izq}" y1="{y:.1f}" '
            f'x2="{ANCHO - margen_der:.0f}" y2="{y:.1f}"/>'
            f'<text class="g-eje" x="{margen_izq - 8:.0f}" y="{y:.1f}" '
            f'text-anchor="end" dominant-baseline="central">{pos}</text>'
        )

    # Etiquetas del eje X: las tres primeras letras de cada carrera.
    for i, carrera in enumerate(carreras):
        partes.append(
            f'<text class="g-eje" x="{px(i):.1f}" y="{alto - 12:.1f}" '
            f'text-anchor="middle">{_escapar(carrera[:3].upper())}</text>'
        )

    for nombre in participantes:
        propio = historial[historial["Participante"] == nombre]
        puntos_linea, marcadores = [], []
        for i, carrera in enumerate(carreras):
            fila = propio[propio["Carrera"] == carrera]
            if fila.empty:
                continue
            pos = int(fila["Posición"].values[0])
            x, y = px(i), py(pos)
            puntos_linea.append(f"{x:.1f},{y:.1f}")
            marcadores.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2">'
                f'<title>{_escapar(nombre)} · {_escapar(carrera)}: P{pos}</title>'
                f'</circle>')
        if len(puntos_linea) < 2:
            continue
        color = color_participante(nombre)
        partes.append(
            f'<g class="g-serie" style="--c:{color}" '
            f'data-participante="{_escapar(nombre)}" tabindex="0">'
            f'<title>{_escapar(nombre)}</title>'
            f'<polyline class="g-linea-hit" points="{" ".join(puntos_linea)}"/>'
            f'<polyline class="g-linea" points="{" ".join(puntos_linea)}"/>'
            f'{"".join(marcadores)}</g>'
        )

    partes.append("</svg>")
    return "".join(partes)


def sparkline(participante: str, all_rankings: pd.DataFrame) -> str:
    """Puntos carrera a carrera de una persona, en chico.

    A diferencia del anterior, no se escribe el numero arriba de cada punto:
    un valor por marca convierte al grafico en una tabla mal dibujada. Va el
    ultimo valor como etiqueta directa y el resto en el tooltip.
    """
    datos = all_rankings[all_rankings["Participante"] == participante]
    if datos.empty:
        return ""

    carreras = carreras_en_orden(datos["Carrera"].unique().tolist())
    valores = []
    for c in carreras:
        fila = datos[datos["Carrera"] == c]
        valores.append(int(fila["Puntos"].values[0]) if not fila.empty else 0)
    if len(valores) < 2:
        return ""

    ancho, alto = 320.0, 68.0
    margen_der = 26.0
    maximo = max(valores) or 1
    util_x, util_y = ancho - margen_der - 4, alto - 22

    def px(i):
        return 4 + util_x * i / max(1, len(valores) - 1)

    def py(v):
        return 8 + util_y * (1 - v / maximo)

    linea = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(valores))
    area = (f"{px(0):.1f},{alto - 14:.1f} " + linea +
            f" {px(len(valores) - 1):.1f},{alto - 14:.1f}")
    color = color_participante(participante)

    marcas = "".join(
        f'<circle class="s-punto" cx="{px(i):.1f}" cy="{py(v):.1f}" r="3">'
        f'<title>{_escapar(carreras[i])}: {v} puntos</title></circle>'
        for i, v in enumerate(valores))

    ultimo_x, ultimo_y = px(len(valores) - 1), py(valores[-1])
    return (
        f'<svg class="g-spark" style="--c:{color}" viewBox="0 0 {ancho:.0f} {alto:.0f}" '
        f'role="img" width="100%" preserveAspectRatio="xMidYMid meet" '
        f'aria-label="Puntos por carrera de {_escapar(participante)}">'
        f'<polygon class="s-area" points="{area}"/>'
        f'<polyline class="s-linea" points="{linea}"/>'
        f'{marcas}'
        f'<text class="s-ultimo" x="{ultimo_x + 7:.1f}" y="{ultimo_y:.1f}" '
        f'dominant-baseline="central">{valores[-1]}</text>'
        f'<text class="g-eje" x="4" y="{alto - 3:.0f}">{_escapar(carreras[0][:3].upper())}</text>'
        f'<text class="g-eje" x="{ultimo_x:.1f}" y="{alto - 3:.0f}" '
        f'text-anchor="end">{_escapar(carreras[-1][:3].upper())}</text>'
        f'</svg>'
    )
