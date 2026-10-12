# -*- coding: utf-8 -*-
"""Pestaña Final: el podio de la temporada y "Tu temporada" de cada uno.

Se desbloquea sola cuando se puntúa la última carrera del calendario. Hasta
entonces muestra cuánto falta y quién sigue con chances matemáticas.

Para revisarla antes de tiempo, con los datos de hoy como si la temporada
hubiera terminado: abrir la página con `?final=1` al final de la dirección.

Los cálculos (funciones sin HTML) están separados del armado, para poder
probarlos con datos chicos.
"""

import html
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from .analisis import cara_a_cara, carreras_totales, proyeccion_titulo
from .config import CALENDARIO, COL_PUESTOS
from .normalizacion import normalizar_piloto
from .paleta import color_participante, hex_a_rgba
from .scoring import cuantas_posiciones_exactas, pilotos_fuera_del_top10


# ---- Cálculos ---------------------------------------------------------------

def temporada_terminada(carreras_jugadas: int) -> bool:
    return carreras_jugadas >= carreras_totales()


def ganadores_por_carrera(all_rankings: pd.DataFrame) -> Dict[str, List[str]]:
    """Quién ganó cada carrera (más de uno si empataron arriba)."""
    ganadores = {}
    for carrera, sub in all_rankings.groupby("Carrera"):
        maximo = sub["Puntos"].max()
        ganadores[carrera] = sorted(sub.loc[sub["Puntos"] == maximo, "Participante"])
    return ganadores


def resumen_podio(ranking_acumulado: pd.DataFrame, all_rankings: pd.DataFrame,
                  badges: Dict[str, List[Dict]]) -> List[Dict]:
    """Los tres primeros, con lo que se muestra al tocar cada escalón."""
    ganadores = ganadores_por_carrera(all_rankings)
    podio = []
    for fila in ranking_acumulado.sort_values("Posición").head(3).itertuples(index=False):
        nombre = str(fila.Participante)
        # reset_index: all_rankings junta una tabla por carrera y repite los
        # índices, así que idxmax() podía devolver varias filas.
        suyas = all_rankings[all_rankings["Participante"] == nombre].reset_index(drop=True)
        mejor = suyas.loc[suyas["Puntos"].idxmax()] if not suyas.empty else None
        podio.append({
            "posicion": int(fila.Posición),
            "participante": nombre,
            "puntos": int(fila.Puntos),
            "carreras_ganadas": sum(1 for g in ganadores.values() if nombre in g),
            "logros": len(badges.get(nombre, [])),
            "mejor_carrera": None if mejor is None else str(mejor["Carrera"]),
            "mejor_puntos": None if mejor is None else int(mejor["Puntos"]),
        })
    return podio


def tu_temporada(participante: str, all_rankings: pd.DataFrame,
                 all_dfs: List[pd.DataFrame], ranking_acumulado: pd.DataFrame) -> Dict:
    """La tarjeta de fin de año de una persona."""
    suyas = all_rankings[all_rankings["Participante"] == participante].reset_index(drop=True)
    filas = [df[df["Participante"] == participante] for df in all_dfs]
    filas = pd.concat(filas) if filas else pd.DataFrame()

    # Piloto fetiche: a quién puso primero más veces.
    primeros = Counter(normalizar_piloto(str(p)).strip()
                       for p in filas.get("Primer puesto", pd.Series(dtype=str)).dropna()
                       if str(p).strip())
    fetiche = primeros.most_common(1)[0] if primeros else None

    # El que más lo traicionó: lo puso en su top 10 y terminó afuera.
    traiciones = Counter(p for d in filas.get("Detalles", pd.Series(dtype=str))
                         for p in pilotos_fuera_del_top10(d))
    traidor = traiciones.most_common(1)[0] if traiciones else None

    exactos = sum(cuantas_posiciones_exactas(d) for d in filas.get("Detalles", []))
    exactos_de_todos = {}
    for df in all_dfs:
        for p, d in zip(df["Participante"], df["Detalles"]):
            exactos_de_todos[p] = exactos_de_todos.get(p, 0) + cuantas_posiciones_exactas(d)
    promedio = (sum(exactos_de_todos.values()) / len(exactos_de_todos)) if exactos_de_todos else 0

    ganadores = ganadores_por_carrera(all_rankings)

    # Némesis: el rival contra el que más carreras perdió (si le ganó menos).
    rivales = cara_a_cara(all_rankings).get(participante, [])
    contra = [r for r in rivales if r["perdio"] > r["gano"]]
    nemesis = max(contra, key=lambda r: (r["perdio"] - r["gano"], r["perdio"]), default=None)

    puesto = ranking_acumulado.loc[ranking_acumulado["Participante"] == participante, "Posición"]

    return {
        "participante": participante,
        "puesto": int(puesto.iloc[0]) if not puesto.empty else None,
        "puntos": int(suyas["Puntos"].sum()),
        "carreras": int(len(suyas)),
        "carreras_ganadas": sum(1 for g in ganadores.values() if participante in g),
        "mejor": None if suyas.empty else (str(suyas.loc[suyas["Puntos"].idxmax(), "Carrera"]),
                                           int(suyas["Puntos"].max())),
        "peor": None if suyas.empty else (str(suyas.loc[suyas["Puntos"].idxmin(), "Carrera"]),
                                          int(suyas["Puntos"].min())),
        "fetiche": fetiche,
        "traidor": traidor,
        "exactos": exactos,
        "exactos_promedio": round(promedio, 1),
        "nemesis": nemesis,
    }


# ---- HTML -------------------------------------------------------------------

def _e(texto) -> str:
    return html.escape(str(texto))


def _fecha_ultima_carrera() -> Optional[str]:
    fechas = [e["FechaISO"] for e in CALENDARIO if e.get("FechaISO")]
    return max(fechas, key=lambda f: datetime.fromisoformat(f)) if fechas else None


def _podio_html(podio: List[Dict]) -> str:
    medallas = {1: "🥇", 2: "🥈", 3: "🥉"}
    escalones = {}
    for p in podio:
        nombre = p["participante"]
        color = color_participante(nombre)
        mejor = (f"{_e(p['mejor_carrera'])} ({p['mejor_puntos']} pts)"
                 if p["mejor_carrera"] else "—")
        escalones[p["posicion"]] = f"""
        <button class="fin-escalon fin-escalon-{p['posicion']}" type="button"
                style="--c:{color};--c-suave:{hex_a_rgba(color, 0.18)}"
                onclick="this.classList.toggle('abierto')" aria-label="{_e(nombre)}, puesto {p['posicion']}">
            <span class="fin-medalla">{medallas[p['posicion']]}</span>
            <span class="fin-nombre">{_e(nombre)}</span>
            <span class="fin-puntos">{p['puntos']} <small>pts</small></span>
            <span class="fin-bloque"><span class="fin-num">{p['posicion']}</span></span>
            <span class="fin-detalle">
                <span>🏁 {p['carreras_ganadas']} carrera{'s' if p['carreras_ganadas'] != 1 else ''} ganada{'s' if p['carreras_ganadas'] != 1 else ''}</span>
                <span>🏅 {p['logros']} logro{'s' if p['logros'] != 1 else ''}</span>
                <span>⭐ Mejor: {mejor}</span>
            </span>
        </button>"""
    campeon = next((p for p in podio if p["posicion"] == 1), None)
    color_campeon = color_participante(campeon["participante"]) if campeon else "#FFD700"
    return f"""
    <div class="fin-podio" data-confeti="{color_campeon}">
        {escalones.get(2, '')}{escalones.get(1, '')}{escalones.get(3, '')}
    </div>
    <p class="fin-ayuda">Tocá cada escalón para ver su temporada</p>"""


def _tarjeta_html(t: Dict, indice: int) -> str:
    nombre = t["participante"]
    color = color_participante(nombre)
    filas = []

    def fila(icono, titulo, valor):
        filas.append(f'<div class="fin-dato"><span class="fin-dato-ico">{icono}</span>'
                     f'<span class="fin-dato-tit">{titulo}</span>'
                     f'<span class="fin-dato-val">{valor}</span></div>')

    if t["fetiche"]:
        fila("❤️", "Tu piloto fetiche",
             f"{_e(t['fetiche'][0])} <small>· lo pusiste 1º {t['fetiche'][1]} veces</small>")
    if t["traidor"]:
        fila("🗡️", "El que más te traicionó",
             f"{_e(t['traidor'][0])} <small>· {t['traidor'][1]} veces fuera del top 10</small>")
    if t["mejor"]:
        fila("🚀", "Tu mejor carrera", f"{_e(t['mejor'][0])} <small>· {t['mejor'][1]} pts</small>")
    if t["peor"]:
        fila("🧱", "Tu peor carrera", f"{_e(t['peor'][0])} <small>· {t['peor'][1]} pts</small>")
    comparacion = ("arriba" if t["exactos"] > t["exactos_promedio"]
                   else "abajo" if t["exactos"] < t["exactos_promedio"] else "justo en")
    fila("🎯", "Aciertos exactos",
         f"{t['exactos']} <small>· {comparacion} del promedio familiar ({t['exactos_promedio']})</small>")
    if t["nemesis"]:
        n = t["nemesis"]
        fila("😤", "Tu némesis",
             f"{_e(n['rival'])} <small>· te ganó {n['perdio']} de {n['gano'] + n['perdio'] + n['empato']}</small>")
    else:
        fila("😎", "Tu némesis", "Nadie: no hay rival que te haya ganado más de lo que le ganaste")

    puesto = f"{t['puesto']}º" if t["puesto"] else "—"
    return f"""
    <article class="fin-tarjeta" id="fin-tarjeta-{indice}" data-i="{indice}"
             style="--c:{color};--c-suave:{hex_a_rgba(color, 0.16)}" hidden>
        <header class="fin-tarjeta-cab">
            <span class="fin-tarjeta-sub">Tu temporada 2026</span>
            <span class="fin-tarjeta-nombre">{_e(nombre)}</span>
            <span class="fin-tarjeta-resumen">
                <b>{puesto}</b> · {t['puntos']} pts · {t['carreras']} carreras ·
                {t['carreras_ganadas']} ganada{'s' if t['carreras_ganadas'] != 1 else ''}
            </span>
        </header>
        <div class="fin-datos">{''.join(filas)}</div>
        <footer class="fin-tarjeta-pie">F1 Predictions · Torneo familiar</footer>
    </article>"""


def generar_panel_final(ranking_acumulado: pd.DataFrame, all_rankings: pd.DataFrame,
                        all_dfs: List[pd.DataFrame], badges: Dict[str, List[Dict]]) -> str:
    """La pestaña entera. Vacía si todavía no hay ninguna carrera."""
    if ranking_acumulado.empty or all_rankings.empty:
        return ""

    jugadas = all_rankings["Carrera"].nunique()
    terminada = temporada_terminada(jugadas)

    podio = resumen_podio(ranking_acumulado, all_rankings, badges)
    participantes = list(ranking_acumulado.sort_values("Posición")["Participante"])
    tarjetas = [tu_temporada(p, all_rankings, all_dfs, ranking_acumulado) for p in participantes]

    selector = "".join(
        f'<button class="fin-chip" type="button" onclick="finMostrar({i})" '
        f'style="--c:{color_participante(t["participante"])}">{_e(t["participante"])}</button>'
        for i, t in enumerate(tarjetas))

    contenido = f"""
    <div class="fin-contenido">
        <h3 class="subsection-heading">El podio</h3>
        {_podio_html(podio)}
        <div class="divider"></div>
        <h3 class="subsection-heading">Tu temporada</h3>
        <p class="section-label" style="margin-bottom:12px;">Elegí tu nombre · después la podés bajar como imagen y mandarla al grupo</p>
        <div class="fin-chips">{selector}</div>
        <div class="fin-tarjetas">{''.join(_tarjeta_html(t, i) for i, t in enumerate(tarjetas))}</div>
        <div class="export-bar" style="margin-top:12px;">
            <button class="export-btn primary" id="fin-bajar" type="button" onclick="finBajar()" hidden>⬇ Bajar mi tarjeta</button>
        </div>
    </div>"""

    if terminada:
        espera = ""
    else:
        faltan = carreras_totales() - jugadas
        vivos = [p for p in proyeccion_titulo(ranking_acumulado, jugadas) if p["vivo"]]
        nombres = ", ".join(_e(p["participante"]) for p in vivos)
        espera = f"""
    <div class="fin-espera">
        <div class="fin-espera-ico">🏁</div>
        <p class="fin-espera-tit">La Final se abre sola cuando termine la última carrera</p>
        <p class="fin-espera-sub">Faltan <b>{faltan}</b> carrera{'s' if faltan != 1 else ''}
           · se corre el <span data-fecha="{_fecha_ultima_carrera() or ''}"></span></p>
        <p class="fin-espera-sub">Con chances matemáticas de salir campeón:
           <b>{len(vivos)}</b> · {nombres}</p>
    </div>"""

    return f"""
<div id="panel-final" class="tab-panel" data-terminada="{'1' if terminada else '0'}">
    <h2 class="section-heading">La <span>Final</span></h2>
    <p class="section-label" style="margin-bottom:18px;">Temporada 2026 · {jugadas} de {carreras_totales()} carreras</p>
    {espera}
    <div class="fin-revelado" {'' if terminada else 'hidden'}>{contenido}</div>
</div>"""
