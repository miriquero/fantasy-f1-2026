# -*- coding: utf-8 -*-
"""Panel de perfiles individuales, selector, Hall of Fame y estadisticas."""

import pandas as pd
from typing import Dict, List

from .calendario import carreras_en_orden
from .charts import generar_sparkline_perfil
from .config import COLORES_PARTICIPANTES, hex_to_rgba
from .scoring import calcular_historial_posiciones

def generar_perfiles_html(all_rankings: pd.DataFrame, all_dfs: List[pd.DataFrame],
                           ranking_acumulado: pd.DataFrame,
                           badges_por_participante: Dict[str, List[Dict]]) -> str:
    if all_rankings.empty or ranking_acumulado.empty:
        return '<p class="empty-msg">Sin datos disponibles.</p>'

    historial_pos = calcular_historial_posiciones(all_rankings)
    df_all = pd.concat(all_dfs) if all_dfs else pd.DataFrame()
    carreras_lista = carreras_en_orden(all_rankings['Carrera'].unique().tolist())
    total_carreras = len(carreras_lista)

    perfiles_html = ""
    for idx, (_, acum_row) in enumerate(ranking_acumulado.iterrows()):
        email    = acum_row['Dirección de correo electrónico']
        nombre   = email.split('@')[0]
        pos_gral = int(acum_row['Posición'])
        pts_tot  = int(acum_row['Puntos'])
        color    = COLORES_PARTICIPANTES[idx % len(COLORES_PARTICIPANTES)]

        data_part = all_rankings[all_rankings["Dirección de correo electrónico"] == email]
        pts_por_carrera = [data_part[data_part['Carrera'] == c]['Puntos'].values[0]
                           if c in data_part['Carrera'].values else 0
                           for c in carreras_lista]
        mejor_pts = max(pts_por_carrera) if pts_por_carrera else 0
        promedio  = round(sum(pts_por_carrera) / len(pts_por_carrera), 1) if pts_por_carrera else 0

        pos_hist = []
        if not historial_pos.empty:
            for c in carreras_lista:
                row_h = historial_pos[(historial_pos["Dirección de correo electrónico"] == email) &
                                      (historial_pos["Carrera"] == c)]
                pos_hist.append(int(row_h["Posición"].values[0]) if not row_h.empty else None)

        racha_max = 0; racha_actual = 0
        for k in range(1, len(pos_hist)):
            if pos_hist[k] is not None and pos_hist[k-1] is not None:
                if pos_hist[k] < pos_hist[k-1]:
                    racha_actual += 1; racha_max = max(racha_max, racha_actual)
                else:
                    racha_actual = 0

        exactos_total = 0
        if not df_all.empty:
            part_df = df_all[df_all["Dirección de correo electrónico"] == email]
            for _, r in part_df.iterrows():
                exactos_total += sum(1 for d in str(r['Detalles']).split('<br>') if 'Exacto en P' in d)

        spark_b64  = generar_sparkline_perfil(email, all_rankings)
        spark_html = (f'<img src="data:image/png;base64,{spark_b64}" alt="Puntos por carrera" class="spark-img">') if spark_b64 else ""

        hist_rows = ""
        for c in carreras_lista:
            row_h = historial_pos[(historial_pos["Dirección de correo electrónico"] == email) &
                                  (historial_pos["Carrera"] == c)]
            pos_c = int(row_h["Posición"].values[0]) if not row_h.empty else "—"
            pts_c = int(data_part[data_part['Carrera'] == c]['Puntos'].values[0]) \
                    if c in data_part['Carrera'].values else "—"
            medal_c = "🥇" if pos_c == 1 else ("🥈" if pos_c == 2 else ("🥉" if pos_c == 3 else ""))
            hist_rows += (f"<tr><td class='cal-carrera'>{c}</td>"
                          f"<td>{medal_c} P{pos_c}</td>"
                          f"<td><span class='pts-chip'>{pts_c}</span></td></tr>")

        badges = badges_por_participante.get(email, [])
        n_badges = len(badges)
        if badges:
            nivel_order = ["BRONCE", "PLATA", "ORO", "LEGENDARIO", "CAMPEÓN"]
            chips = ""
            for nivel in nivel_order:
                grupo = [b for b in badges if b.get("nivel") == nivel]
                for b in grupo:
                    bg       = hex_to_rgba(b["hex"], 0.18)
                    border   = hex_to_rgba(b["hex"], 0.40)
                    desc_safe = b["desc"].replace('"', '&quot;')
                    chips += (
                        f'<button class="badge-chip" '
                        f'style="background:{bg};border:1px solid {border};color:{b["hex"]};" '
                        f'data-desc="{desc_safe}" '
                        f'onclick="toggleBadge(this)" '
                        f'onmouseenter="showBadge(this)" '
                        f'onmouseleave="hideBadge(this)">'
                        f'<span class="badge-emoji">{b["emoji"]}</span>'
                        f'<span class="badge-nombre">{b["nombre"]}</span>'
                        f'<span class="badge-nivel-tag">{b.get("nivel_emoji","")}</span>'
                        f'</button>'
                    )
            badges_section = (
                f'<div class="perfil-badges-wrap">'
                f'<div class="section-label" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">'
                f'LOGROS '
                f'<span class="badge-counter">{n_badges}/15</span>'
                f'<span class="badge-hint">Tocá para ver qué significa</span>'
                f'</div>'
                f'<div class="badges-row">{chips}</div>'
                f'</div>'
            )
        else:
            badges_section = (
                '<div class="perfil-badges-wrap">'
                '<div class="section-label" style="display:flex;align-items:center;gap:8px;">'
                'LOGROS <span class="badge-counter">0/15</span>'
                '</div>'
                '<p class="empty-msg" style="padding:8px 0;font-size:0.8rem;">'
                'Seguí participando para desbloquear logros 🏁</p>'
                '</div>'
            )

        if pos_gral == 1:   medal_str = '<span class="medal gold">1</span>'
        elif pos_gral == 2: medal_str = '<span class="medal silver">2</span>'
        elif pos_gral == 3: medal_str = '<span class="medal bronze">3</span>'
        else:               medal_str = f'<span class="medal plain">{pos_gral}</span>'

        perfiles_html += f"""
        <div class="perfil-card reveal" id="perfil-{idx}">
            <div class="perfil-header" style="border-left:4px solid {color};">
                <div class="perfil-avatar" style="background:{hex_to_rgba(color,0.13)};color:{color};border:1px solid {hex_to_rgba(color,0.27)};">{nombre[:2].upper()}</div>
                <div class="perfil-info">
                    <div class="perfil-nombre">{nombre}</div>
                    <div class="perfil-email">{email}</div>
                </div>
                <div class="perfil-pos-wrap">
                    {medal_str}
                    <span class="perfil-pts" style="color:{color};">{pts_tot} <span style="font-size:0.7rem;color:var(--muted);">pts</span></span>
                </div>
            </div>

            <div class="perfil-stats-mini">
                <div class="perfil-stat"><div class="perfil-stat-num">{promedio}</div><div class="perfil-stat-label">Prom.</div></div>
                <div class="perfil-stat"><div class="perfil-stat-num">{mejor_pts}</div><div class="perfil-stat-label">Mejor</div></div>
                <div class="perfil-stat"><div class="perfil-stat-num">{exactos_total}</div><div class="perfil-stat-label">Exactos</div></div>
                <div class="perfil-stat"><div class="perfil-stat-num">{racha_max}</div><div class="perfil-stat-label">Racha</div></div>
            </div>

            {badges_section}

            <div class="perfil-spark-wrap">
                <div class="section-label">PUNTOS POR CARRERA</div>
                {spark_html}
            </div>

            <div class="perfil-hist-toggle">
                <button class="detail-toggle" onclick="toggleDetail('phist-{idx}')">
                    <span>Ver historial completo ({total_carreras} carreras)</span>
                    <span class="toggle-icon" id="icon-phist-{idx}">＋</span>
                </button>
                <div id="phist-{idx}" class="detail-body">
                    <div class="table-wrapper" style="margin-top:12px;">
                        <table class="data-table">
                            <thead><tr><th>Gran Premio</th><th>Posición</th><th>Puntos</th></tr></thead>
                            <tbody>{hist_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div class="perfil-export-bar">
                <button class="export-btn export-btn-sm" onclick="exportarPerfil(this, {idx}, '{nombre}')">
                    📸 Exportar tarjeta
                </button>
            </div>
        </div>
        """

    return perfiles_html
def generar_perfil_selector_html(ranking_acumulado: pd.DataFrame) -> str:
    """Genera botones de selección para filtrar perfiles por participante."""
    if ranking_acumulado.empty:
        return ""
    btns = '<button class="perfil-sel-btn all-btn active" onclick="filtrarPerfil(this, \'all\')">Todos</button>'
    for idx, (_, row) in enumerate(ranking_acumulado.iterrows()):
        nombre = row["Dirección de correo electrónico"].split("@")[0]
        btns += f'<button class="perfil-sel-btn" onclick="filtrarPerfil(this, {idx})">{nombre}</button>'
    return btns
HALL_OF_FAME = [
    {
        "temporada": "2025",
        "nombre": "RIQUEROLE",
        "stats": [
            {"num": "👑", "label": "Campeón"},
            {"num": "2025", "label": "Temporada"},
        ]
    },
]
def generar_hof_panel_html() -> str:
    """Genera el panel Hall of Fame con los campeones históricos."""
    bloques = ""
    for entry in HALL_OF_FAME:
        stats_html = "".join([
            f'''<div class="hof-stat">
                <div class="hof-stat-num">{s["num"]}</div>
                <div class="hof-stat-label">{s["label"]}</div>
            </div>'''
            for s in entry.get("stats", [])
        ])
        bloques += f'''
        <div class="hof-year-block">
            <div class="hof-year-title">Temporada {entry["temporada"]}</div>
            <div class="hof-card reveal">
                <div class="hof-crown">👑</div>
                <div class="hof-info">
                    <div class="hof-nombre">{entry["nombre"]}</div>
                    <div class="hof-temporada">Campeón de la Temporada {entry["temporada"]}</div>
                    <div class="hof-stats-row">{stats_html}</div>
                </div>
                <div class="hof-trophy">🏆</div>
            </div>
        </div>
        '''

    return f'''
<h3 class="subsection-heading" id="mas-historia">Historia</h3>
<p class="section-label" style="margin-bottom:24px;">Campeones históricos del Fantasy F1 familiar</p>
<div class="hof-wrap">
    {bloques}
</div>
'''
def generar_estadisticas_adicionales(all_dfs: List[pd.DataFrame],
                                      ranking_acumulado: pd.DataFrame) -> str:
    if not all_dfs:
        return '<p class="empty-msg">No hay datos disponibles.</p>'

    df_all = pd.concat(all_dfs)
    total_participantes = df_all['Dirección de correo electrónico'].nunique()
    total_predicciones  = len(df_all)
    puntos_totales      = df_all['Puntos'].sum()
    promedio_puntos     = puntos_totales / total_predicciones if total_predicciones > 0 else 0
    lider = ranking_acumulado.iloc[0]['Dirección de correo electrónico'] \
            if not ranking_acumulado.empty else "N/A"

    orden_carreras = carreras_en_orden(df_all['Carrera'].unique().tolist())
    maximos_por_carrera = df_all.groupby('Carrera')['Puntos'].max()
    maximos_por_carrera = maximos_por_carrera.reindex(orden_carreras)

    maximos_rows = "".join([
        f'<tr><td class="stat-label">{c}</td>'
        f'<td class="stat-value">{p} <span class="pts-tag">pts</span></td></tr>'
        for c, p in maximos_por_carrera.items() if pd.notna(p)
    ])

    return f"""
    <div class="stats-grid">
        <div class="stat-card accent reveal"><div class="stat-num" data-countup>{total_participantes}</div><div class="stat-desc">Participantes</div></div>
        <div class="stat-card reveal"><div class="stat-num" data-countup>{total_predicciones}</div><div class="stat-desc">Predicciones totales</div></div>
        <div class="stat-card reveal"><div class="stat-num" data-countup>{puntos_totales}</div><div class="stat-desc">Puntos distribuidos</div></div>
        <div class="stat-card reveal"><div class="stat-num" data-countup>{promedio_puntos:.1f}</div><div class="stat-desc">Promedio por predicción</div></div>
    </div>
    <div class="leader-banner">
        <span class="leader-label">LÍDER ACTUAL</span>
        <span class="leader-name">{lider.split('@')[0]}</span>
        <span class="leader-email">{lider}</span>
    </div>
    <div class="section-label">MÁXIMOS POR CARRERA</div>
    <div class="table-wrapper">
        <table class="data-table">
            <thead><tr><th>Carrera</th><th>Mejor puntaje</th></tr></thead>
            <tbody>{maximos_rows}</tbody>
        </table>
    </div>
    """
