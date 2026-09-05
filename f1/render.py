# -*- coding: utf-8 -*-
"""Arma los fragmentos de HTML y los renderiza con la plantilla Jinja2."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import pandas as pd
from jinja2 import Environment, FileSystemLoader

from .badges import generar_logros_panel_html
from .calendario import generar_calendario_visual, obtener_proxima_carrera

DIR_TEMPLATES = Path(__file__).parent / "templates"

_entorno = None


def _plantilla():
    """Carga el entorno de Jinja2 una sola vez y lo reutiliza."""
    global _entorno
    if _entorno is None:
        _entorno = Environment(
            loader=FileSystemLoader(str(DIR_TEMPLATES)),
            autoescape=False,      # los fragmentos ya llegan como HTML armado
        )
    return _entorno.get_template("ranking.html.j2")


def _leer_asset(nombre: str) -> str:
    """Lee un CSS o JS de templates/ tal cual, sin pasarlo por Jinja2."""
    return (DIR_TEMPLATES / nombre).read_text(encoding="utf-8")


def generar_html(rankings_por_carrera: List[pd.DataFrame],
                 ranking_acumulado: pd.DataFrame,
                 grafico_barras: str,
                 stats_adicionales: str,
                 perfiles_html: str,
                 badges_por_participante: Dict[str, List[Dict]],
                 perfil_selector_html: str = "",
                 hof_panel_html: str = "") -> str:

    proxima_carrera, proxima_iso = obtener_proxima_carrera()

    # ---- Onboarding colapsable ----
    onboarding_html = """
    <div class="onboarding" id="onboarding">
        <button class="onboarding-toggle" onclick="toggleOnboarding()">
            <span>¿Cómo funciona el torneo?</span>
            <span class="onboarding-icon">+</span>
        </button>
        <div class="onboarding-body">
            Cada participante predice el orden de los primeros 10 puestos antes de cada carrera.
            Se suman puntos por acertar la posición exacta y puntos extra por acertar el ganador.
            Los <b>logros</b> se desbloquean automáticamente según tu desempeño acumulado — mirá la
            pestaña Logros para ver los 15 disponibles.
        </div>
    </div>"""

    # ---- Ranking acumulado ----
    if not ranking_acumulado.empty:
        top3 = ranking_acumulado[ranking_acumulado['Posición'] <= 3]
        resto = ranking_acumulado[ranking_acumulado['Posición'] > 3]

        # --- Podio destacado (top 3) ---
        podium_html = ""
        if not top3.empty:
            medal_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}
            cards = {}
            for _, row in top3.iterrows():
                pos = int(row['Posición']); email = row['Dirección de correo electrónico']
                nombre = email.split('@')[0]; pts = row['Puntos']
                iniciales = nombre[:2].upper()
                cards[pos] = f"""
                <div class="podium-card podium-{pos}" data-pos="{pos}" onclick="irPerfil({pos-1})" style="cursor:pointer;" title="Ver perfil de {nombre}">
                    <div class="podium-shine"></div>
                    <div class="podium-medal">{medal_emoji.get(pos,'')}</div>
                    <div class="podium-avatar">{iniciales}</div>
                    <div class="podium-nombre">{nombre}</div>
                    <div class="podium-pts" data-countup>{pts}</div>
                    <div class="podium-pts-label">puntos</div>
                    <div class="podium-base"></div>
                </div>"""
            podium_html = f"""
            <div class="podium">
                {cards.get(2,'')}
                {cards.get(1,'')}
                {cards.get(3,'')}
            </div>"""

        # --- Tabla del resto (4° en adelante) ---
        tabla_resto_html = ""
        if not resto.empty:
            rows_html = ""
            for _, row in resto.iterrows():
                pos = row['Posición']; email = row['Dirección de correo electrónico']
                nombre = email.split('@')[0]; pts = row['Puntos']
                cambio = row.get('Cambio', '—')
                rows_html += f"""
                <tr class="row-reveal" onclick="irPerfil({int(pos)-1})" style="cursor:pointer;" title="Ver perfil de {nombre}">
                    <td><span class="medal plain">{pos}</span></td>
                    <td><span class="driver-name">{nombre}</span><span class="driver-email">{email}</span></td>
                    <td><span class="pts-big">{pts}</span></td>
                    <td>{cambio}</td>
                </tr>"""
            tabla_resto_html = f"""
            <div class="table-wrapper">
            <table class="data-table leaderboard">
                <thead><tr><th>#</th><th>Participante</th><th>Puntos</th><th>Cambio</th></tr></thead>
                <tbody>{rows_html}</tbody>
            </table></div>"""

        ranking_acumulado_html = f"""
        {onboarding_html}
        <p class="section-label" style="margin-bottom:8px;color:var(--muted);">Tocá una fila o el podio para ver el perfil</p>
        {podium_html}
        {tabla_resto_html}"""
    else:
        ranking_acumulado_html = onboarding_html + '<p class="empty-msg">No hay datos disponibles.</p>'

    # ---- Rankings por carrera ----
    rankings_por_carrera_html = ""
    for i, ranking in enumerate(rankings_por_carrera):
        carrera = ranking["Carrera"].iloc[0]
        table_rows = ""
        for j, row in ranking.iterrows():
            email = row['Dirección de correo electrónico']; pts = row['Puntos']
            table_rows += (f"<tr><td>{row['Posición']}</td>"
                           f"<td>{email.split('@')[0]}<span class='driver-email'>{email}</span></td>"
                           f"<td><span class='pts-chip'>{pts}</span></td></tr>")
        detalles_html = ""
        for j, row in ranking.iterrows():
            email = row["Dirección de correo electrónico"]; detalles = row["Detalles"]
            detalles_html += f"""
            <div class="detail-row">
                <button class="detail-toggle" onclick="toggleDetail('det-{i}-{j}')">
                    <span>{email.split('@')[0]}</span>
                    <span class="toggle-icon" id="icon-det-{i}-{j}">＋</span>
                </button>
                <div id="det-{i}-{j}" class="detail-body">
                    <p class="detail-text">{detalles}</p>
                </div>
            </div>"""
        rankings_por_carrera_html += f"""
        <div class="race-block">
            <button class="race-header" onclick="toggleDetail('race-{i}')">
                <div class="race-title-wrap">
                    <span class="race-badge">R{i+1:02d}</span>
                    <span class="race-title">{carrera}</span>
                </div>
                <span class="toggle-icon" id="icon-race-{i}">＋</span>
            </button>
            <div id="race-{i}" class="race-body">
                <div class="table-wrapper">
                    <table class="data-table">
                        <thead><tr><th>#</th><th>Participante</th><th>Pts</th></tr></thead>
                        <tbody>{table_rows}</tbody>
                    </table>
                </div>
                <div class="section-label" style="margin-top:24px;">DESGLOSE POR PARTICIPANTE</div>
                {detalles_html}
            </div>
        </div>"""

    # ---- Panel de logros ----
    logros_panel_html = generar_logros_panel_html(badges_por_participante)

    # ---- Calendario visual ----
    calendario_html = generar_calendario_visual(proxima_iso)

    graf_barras_html = (f'<img src="data:image/png;base64,{grafico_barras}" alt="Puntos acumulados" class="chart-img">') if grafico_barras else '<p class="empty-msg">Sin datos.</p>'
    fecha_actual     = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y · %H:%M")

    # ---- Nuevos paneles ----
    # perfil_selector_html y hof_panel_html ya llegan como params

    return _plantilla().render(
        CAL_CSS=_leer_asset("calendario.css"),
        LOGROS_CSS=_leer_asset("logros.css"),
        ANIM_CSS=_leer_asset("anim.css"),
        LOGROS_JS=_leer_asset("logros.js"),
        ANIM_JS=_leer_asset("anim.js"),
        proxima_carrera=proxima_carrera,
        proxima_iso=proxima_iso,
        ranking_acumulado_html=ranking_acumulado_html,
        rankings_por_carrera_html=rankings_por_carrera_html,
        logros_panel_html=logros_panel_html,
        calendario_html=calendario_html,
        graf_barras_html=graf_barras_html,
        stats_adicionales=stats_adicionales,
        perfiles_html=perfiles_html,
        perfil_selector_html=perfil_selector_html,
        hof_panel_html=hof_panel_html,
        fecha_actual=fecha_actual,
    )
