import pandas as pd
import os
import json
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime
import numpy as np

# =========================
# CONFIGURACIÓN GENERAL
# =========================
CARPETA_RESPUESTAS = "respuestas"
ARCHIVO_RESULTADOS = "resultados.json"

PILOTOS = [
    "Max Verstappen", "Arvid Lindblad", "Charles Leclerc", "Lewis Hamilton",
    "Oscar Piastri", "Lando Norris", "George Russell", "Kimi Antonelli",
    "Pierre Gasly", "Franco Colapinto", "Carlos Sainz", "Alex Albon",
    "Esteban Ocon", "Ollie Bearman", "Liam Lawson", "Isack Hadjar",
    "Fernando Alonso", "Lance Stroll", "Gabriel Bortoletto", "Nico Hulkenberg",
    "Valtteri Bottas", "Sergio Perez", "Yuki Tsunoda"
]

COL_PUESTOS = [
    "Primer puesto", "Segundo puesto", "Tercer puesto", "Cuarto puesto",
    "Quinto puesto", "Sexto puesto", "Séptimo puesto", "Octavo puesto",
    "Noveno puesto", "Décimo puesto"
]

CALENDARIO = [
    {"Jornada": "R01", "Carrera": "AUSTRALIA", "Fecha": "8 MAR", "Hora Local": "15:00", "Hora Argentina": "01:00"},
    {"Jornada": "R02", "Carrera": "CHINA", "Fecha": "15 MAR", "Hora Local": "15:00", "Hora Argentina": "04:00"},
    {"Jornada": "R03", "Carrera": "JAPÓN", "Fecha": "29 MAR", "Hora Local": "14:00", "Hora Argentina": "02:00"},
    {"Jornada": "<s>R04</s>", "Carrera": "<s>BAHREIN</s>", "Fecha": "<s>12 ABR</s>", "Hora Local": "<s>18:00</s>", "Hora Argentina": "<s>12:00</s>"},
    {"Jornada": "<s>R05</s>", "Carrera": "<s>ARABIA SAUDITA</s>", "Fecha": "<s>19 ABR</s>", "Hora Local": "<s>20:00</s>", "Hora Argentina": "<s>14:00</s>"},
    {"Jornada": "R06", "Carrera": "MIAMI", "Fecha": "03 MAY", "Hora Local": "16:00", "Hora Argentina": "17:00"},
    {"Jornada": "R07", "Carrera": "CANADÁ", "Fecha": "24 MAY", "Hora Local": "16:00", "Hora Argentina": "17:00"},
    {"Jornada": "R08", "Carrera": "MÓNACO", "Fecha": "07 JUN", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R09", "Carrera": "BARCELONA", "Fecha": "14 JUN", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R10", "Carrera": "AUSTRIA", "Fecha": "28 JUN", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R11", "Carrera": "GRAN BRETAÑA", "Fecha": "05 JUL", "Hora Local": "15:00", "Hora Argentina": "11:00"},
    {"Jornada": "R12", "Carrera": "BÉLGICA", "Fecha": "19 JUL", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R13", "Carrera": "HUNGRÍA", "Fecha": "26 JUL", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R14", "Carrera": "PAÍSES BAJOS", "Fecha": "23 AGO", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R15", "Carrera": "ITALIA", "Fecha": "06 SEP", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R16", "Carrera": "MADRID", "Fecha": "13 SEP", "Hora Local": "15:00", "Hora Argentina": "10:00"},
    {"Jornada": "R17", "Carrera": "AZERBAIYÁN", "Fecha": "26 SEP", "Hora Local": "15:00", "Hora Argentina": "08:00"},
    {"Jornada": "R18", "Carrera": "SINGAPUR", "Fecha": "11 OCT", "Hora Local": "20:00", "Hora Argentina": "09:00"},
    {"Jornada": "R19", "Carrera": "AUSTIN", "Fecha": "25 OCT", "Hora Local": "15:00", "Hora Argentina": "17:00"},
    {"Jornada": "R20", "Carrera": "MÉXICO", "Fecha": "01 NOV", "Hora Local": "14:00", "Hora Argentina": "17:00"},
    {"Jornada": "R21", "Carrera": "BRASIL", "Fecha": "08 NOV", "Hora Local": "14:00", "Hora Argentina": "14:00"},
    {"Jornada": "R22", "Carrera": "LAS VEGAS", "Fecha": "21 NOV", "Hora Local": "20:00", "Hora Argentina": "01:00 (Domingo 22)"},
    {"Jornada": "R23", "Carrera": "QATAR", "Fecha": "29 NOV", "Hora Local": "19:00", "Hora Argentina": "13:00"},
    {"Jornada": "R24", "Carrera": "ABU DHABI", "Fecha": "06 DIC", "Hora Local": "17:00", "Hora Argentina": "10:00"}
]

# =========================
# FUNCIÓN PUNTOS POR POSICIÓN
# =========================
def puntos_posicion(predicha: int, real: int) -> int:
    if predicha == real:
        return 10
    elif abs(predicha - real) == 1:
        return 5
    else:
        return 1

# =========================
# CALCULAR PUNTOS Y DETALLES
# =========================
def calcular_puntos_y_detalles(row: pd.Series, posiciones_reales: Dict[str, int], vuelta_rapida_real: str, colapinto_real: int) -> Tuple[int, str]:
    puntos = 0
    detalles = []

    for i, col in enumerate(COL_PUESTOS):
        piloto = str(row.get(col, "")).strip()
        if not piloto:
            continue
        posicion_predicha = i + 1
        if piloto in posiciones_reales:
            posicion_real = posiciones_reales[piloto]
            pts = puntos_posicion(posicion_predicha, posicion_real)
            puntos += pts
            if pts == 10:
                detalles.append(f"{piloto}: Exacto en P{posicion_predicha} (+10)")
            elif pts == 5:
                detalles.append(f"{piloto}: Diff 1 (pred P{posicion_predicha}, real P{posicion_real}) (+5)")
            elif pts == 1:
                detalles.append(f"{piloto}: En top 10 (pred P{posicion_predicha}, real P{posicion_real}) (+1)")

    vr = str(row.get("Vuelta Rápida", "")).strip()
    if vr == vuelta_rapida_real:
        puntos += 10
        detalles.append(f"Vuelta rápida: {vr} (+10)")

    try:
        pred_colapinto_str = str(row.get("Franco Colapinto", "")).strip()
        pred_colapinto = convertir_posicion_a_numero(pred_colapinto_str)
        if pred_colapinto == colapinto_real:
            puntos += 10
            detalles.append(f"Colapinto: EXACTO (+10 puntos)")
        elif abs(pred_colapinto - colapinto_real) == 1:
            puntos += 5
            detalles.append(f"Colapinto: diferencia de 1 (+5 puntos)")
    except (ValueError, TypeError):
        pass

    detalle_str = "<br>".join(detalles) if detalles else "Sin puntos detallados"
    return puntos, detalle_str

# =========================
# CONVERTIR POSICIÓN TEXTUAL A NÚMERO
# =========================
def convertir_posicion_a_numero(pos_str: str) -> int:
    mapa = {
        "Primero": 1, "Segundo": 2, "Tercer": 3, "Cuarto": 4, "Quinto": 5,
        "Sexto": 6, "Séptimo": 7, "Septimo": 7, "Octavo": 8, "Noveno": 9, "Décimo": 10, "Decimo": 10,
        "Undécimo": 11, "Duodécimo": 12, "Décimo Segundo": 12, "Décimo Tercer": 13, "Décimo Tercero": 13,
        "Décimo Cuarto": 14, "Décimo Quinto": 15, "Décimo Sexto": 16, "Décimo Séptimo": 17,
        "Décimo Octavo": 18, "Décimo Noveno": 19, "Vigésimo": 20,
    }
    pos_str_lower = pos_str.lower().replace("puesto", "").strip()
    for key in mapa:
        if key.lower() in pos_str_lower:
            return mapa[key]
    return int(pos_str)

# =========================
# PROCESAR UNA CARRERA
# =========================
def procesar_carrera(nombre_carrera: str, archivo_csv: str, resultados: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(archivo_csv)
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)

    resultado_carrera = resultados.get("resultado_carrera", [])
    vuelta_rapida_real = resultados.get("vuelta_rapida", "")
    colapinto_real = resultados.get("colapinto", 0)

    if isinstance(colapinto_real, str):
        try:
            colapinto_real = convertir_posicion_a_numero(colapinto_real)
        except:
            colapinto_real = 0

    posiciones_reales = {piloto: i+1 for i, piloto in enumerate(resultado_carrera)}

    df[["Puntos", "Detalles"]] = df.apply(
        lambda row: pd.Series(calcular_puntos_y_detalles(row, posiciones_reales, vuelta_rapida_real, colapinto_real)),
        axis=1
    )
    df["Carrera"] = nombre_carrera

    ranking = df.groupby("Dirección de correo electrónico", as_index=False).agg({
        "Puntos": "sum",
        "Detalles": lambda x: "<br><br>".join(x)
    }).sort_values("Puntos", ascending=False).reset_index(drop=True)
    ranking["Posición"] = ranking.index + 1
    ranking = ranking[["Posición", "Dirección de correo electrónico", "Puntos", "Detalles"]]
    ranking["Carrera"] = nombre_carrera

    return ranking, df

# =========================
# CALCULAR CAMBIO DE POSICIONES
# =========================
def calcular_cambios_posiciones(all_rankings: pd.DataFrame, ranking_acumulado: pd.DataFrame) -> pd.DataFrame:
    if len(all_rankings['Carrera'].unique()) < 2:
        ranking_acumulado['Cambio'] = '-'
        return ranking_acumulado

    carreras = sorted(all_rankings['Carrera'].unique())
    acum_actual = all_rankings[all_rankings['Carrera'] == carreras[-1]].set_index('Dirección de correo electrónico')['Posición']

    prev_rankings = all_rankings[all_rankings['Carrera'] != carreras[-1]]
    if prev_rankings.empty:
        acum_prev = pd.Series()
    else:
        acum_prev = prev_rankings.groupby("Dirección de correo electrónico")["Puntos"].sum().sort_values(ascending=False).reset_index()
        acum_prev["Posición"] = acum_prev.index + 1
        acum_prev = acum_prev.set_index('Dirección de correo electrónico')['Posición']

    cambios = {}
    for email in ranking_acumulado['Dirección de correo electrónico']:
        pos_actual = ranking_acumulado[ranking_acumulado['Dirección de correo electrónico'] == email]['Posición'].values[0]
        pos_prev = acum_prev.get(email, float('inf'))
        diff = pos_prev - pos_actual
        if diff > 0:
            cambios[email] = f'<span class="trend-up">▲{diff}</span>'
        elif diff < 0:
            cambios[email] = f'<span class="trend-down">▼{-diff}</span>'
        else:
            cambios[email] = '<span class="trend-neutral">—</span>'

    ranking_acumulado['Cambio'] = ranking_acumulado['Dirección de correo electrónico'].map(cambios)
    return ranking_acumulado

# =========================
# GENERAR GRÁFICOS
# =========================
def generar_grafico_barras_acumulado(ranking_acumulado: pd.DataFrame) -> str:
    if ranking_acumulado.empty:
        return ""

    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots(figsize=(10, max(4, len(ranking_acumulado) * 0.45 + 1)))
    
    colors = ['#E10600' if i == 0 else '#2A2A2A' for i in range(len(ranking_acumulado))]
    bars = ax.barh(
        ranking_acumulado["Dirección de correo electrónico"],
        ranking_acumulado["Puntos"],
        color=colors, height=0.65, edgecolor='none'
    )
    
    for bar, pts in zip(bars, ranking_acumulado["Puntos"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{pts}', va='center', ha='left', color='#FFFFFF', fontsize=9, fontweight='bold')
    
    ax.set_title('Puntos acumulados', color='#FFFFFF', fontsize=13, pad=15, loc='left', fontweight='bold')
    ax.set_xlabel('')
    ax.invert_yaxis()
    ax.tick_params(colors='#AAAAAA', labelsize=9)
    ax.set_facecolor('#0D0D0D')
    fig.patch.set_facecolor('#0D0D0D')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_visible(False)
    ax.xaxis.set_tick_params(color='#333333')
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color='#1E1E1E', linewidth=0.8)
    
    plt.tight_layout(pad=1.5)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=False, dpi=130)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

def generar_grafico_evolucion(all_rankings: pd.DataFrame, top_n=5) -> str:
    if all_rankings.empty:
        return ""

    pivot = all_rankings.pivot_table(index="Dirección de correo electrónico", columns="Carrera", values="Puntos", fill_value=0).cumsum(axis=1)
    top_emails = pivot.iloc[:, -1].nlargest(top_n).index
    carreras_ordenadas = sorted(pivot.columns)
    pivot = pivot[carreras_ordenadas]

    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ['#E10600', '#00C8FF', '#FFD700', '#C77DFF', '#39FF14']
    
    for i, email in enumerate(top_emails):
        label = email.split('@')[0]
        line_color = colors[i % len(colors)]
        ax.plot(pivot.columns, pivot.loc[email], marker='o', linewidth=2.5,
                markersize=7, label=label, color=line_color,
                markerfacecolor='#0D0D0D', markeredgecolor=line_color, markeredgewidth=2)
    
    ax.set_title('Evolución de puntos · Top 5', color='#FFFFFF', fontsize=13, pad=15, loc='left', fontweight='bold')
    ax.set_xlabel('')
    ax.set_ylabel('Puntos acumulados', color='#888888', fontsize=9)
    legend = ax.legend(loc='upper left', frameon=False, labelcolor='#DDDDDD', fontsize=9)
    ax.grid(True, color='#1E1E1E', linestyle='-', linewidth=0.8)
    ax.tick_params(colors='#888888', labelsize=8)
    ax.set_facecolor('#0D0D0D')
    fig.patch.set_facecolor('#0D0D0D')
    for spine in ax.spines.values():
        spine.set_color('#333333')
    
    plt.tight_layout(pad=1.5)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=False, dpi=130)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

def generar_radar_por_carrera(all_dfs: List[pd.DataFrame], top_n=5) -> List[Tuple[str, str]]:
    if not all_dfs:
        return []

    df_all = pd.concat(all_dfs)
    categorias = ['Exactos', 'Cercanos', 'Top10', 'V.Rápida', 'Colapinto']

    def breakdown_puntos(row):
        exactos = sum(1 for d in row['Detalles'].split('<br>') if 'Exacto' in d) * 10
        cercanos = sum(1 for d in row['Detalles'].split('<br>') if 'Diff 1' in d) * 5
        top10 = sum(1 for d in row['Detalles'].split('<br>') if 'En top 10' in d) * 1
        vr = 10 if 'Vuelta rápida' in row['Detalles'] else 0
        col = 0
        if 'Colapinto: EXACTO' in row['Detalles']:
            col = 10
        elif 'Colapinto: diferencia de 1' in row['Detalles']:
            col = 5
        return pd.Series({'Exactos': exactos, 'Cercanos': cercanos, 'Top10': top10, 'VueltaRapida': vr, 'Colapinto': col})

    breakdowns = df_all.apply(breakdown_puntos, axis=1)
    df_with_break = pd.concat([df_all[['Carrera', 'Dirección de correo electrónico', 'Puntos']], breakdowns], axis=1)

    radars = []
    for carrera, group in df_with_break.groupby('Carrera'):
        if group.empty:
            continue
        top_group = group.nlargest(top_n, 'Puntos')
        if top_group.empty:
            continue

        max_por_cat = {'Exactos': 100, 'Cercanos': 50, 'Top10': 10, 'VueltaRapida': 10, 'Colapinto': 10}
        for cat in ['Exactos', 'Cercanos', 'Top10', 'VueltaRapida', 'Colapinto']:
            top_group = top_group.copy()
            top_group[cat] = top_group[cat] / max_por_cat[cat] * 100

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2*np.pi, len(categorias), endpoint=False).tolist()
        angles += angles[:1]

        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        colors = ['#E10600', '#00C8FF', '#FFD700', '#C77DFF', '#39FF14']

        for i, (_, row) in enumerate(top_group.iterrows()):
            values = row[['Exactos', 'Cercanos', 'Top10', 'VueltaRapida', 'Colapinto']].tolist()
            values += values[:1]
            ax.plot(angles, values, linewidth=2, linestyle='solid',
                    label=f"{row['Dirección de correo electrónico'].split('@')[0]} ({int(row['Puntos'])} pts)",
                    color=colors[i % len(colors)])
            ax.fill(angles, values, color=colors[i % len(colors)], alpha=0.12)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categorias, fontsize=10, color='#CCCCCC')
        ax.set_ylim(0, 100)
        ax.set_yticklabels([])
        ax.tick_params(colors='#555555')
        ax.grid(color='#222222', linewidth=0.8)
        ax.set_facecolor('#0D0D0D')
        fig.patch.set_facecolor('#0D0D0D')
        ax.spines['polar'].set_color('#333333')

        ax.set_title(f'Perfil de aciertos · {carrera}\nTop {min(top_n, len(top_group))}',
                     color='#FFFFFF', fontsize=12, pad=25, fontweight='bold')
        ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.12), labelcolor='#CCCCCC',
                  frameon=False, fontsize=8)

        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', transparent=False, dpi=130)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        radars.append((carrera, img_base64))

    return radars

# =========================
# GENERAR ESTADÍSTICAS ADICIONALES
# =========================
def generar_estadisticas_adicionales(all_dfs: List[pd.DataFrame], ranking_acumulado: pd.DataFrame) -> str:
    if not all_dfs:
        return '<p class="empty-msg">No hay datos disponibles.</p>'

    df_all = pd.concat(all_dfs)
    total_participantes = df_all['Dirección de correo electrónico'].nunique()
    total_predicciones = len(df_all)
    puntos_totales = df_all['Puntos'].sum()
    promedio_puntos = puntos_totales / total_predicciones if total_predicciones > 0 else 0
    lider = ranking_acumulado.iloc[0]['Dirección de correo electrónico'] if not ranking_acumulado.empty else "N/A"

    maximos_por_carrera = df_all.groupby('Carrera')['Puntos'].max()
    maximos_rows = "".join([
        f'<tr><td class="stat-label">{carrera}</td><td class="stat-value">{puntos} <span class="pts-tag">pts</span></td></tr>'
        for carrera, puntos in maximos_por_carrera.items()
    ])

    return f"""
    <div class="stats-grid">
        <div class="stat-card accent">
            <div class="stat-num">{total_participantes}</div>
            <div class="stat-desc">Participantes</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">{total_predicciones}</div>
            <div class="stat-desc">Predicciones totales</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">{puntos_totales}</div>
            <div class="stat-desc">Puntos distribuidos</div>
        </div>
        <div class="stat-card">
            <div class="stat-num">{promedio_puntos:.1f}</div>
            <div class="stat-desc">Promedio por predicción</div>
        </div>
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

# =========================
# GENERAR HTML — DISEÑO 2026
# =========================
def generar_html(rankings_por_carrera: List[pd.DataFrame], ranking_acumulado: pd.DataFrame,
                 grafico_barras: str, grafico_evolucion: str, radars_data: List[Tuple[str, str]],
                 stats_adicionales: str) -> str:

    calendario_df = pd.DataFrame(CALENDARIO)

    # ---- Ranking acumulado ----
    if not ranking_acumulado.empty:
        rows_html = ""
        for _, row in ranking_acumulado.iterrows():
            pos = row['Posición']
            email = row['Dirección de correo electrónico']
            nombre = email.split('@')[0]
            pts = row['Puntos']
            cambio = row.get('Cambio', '—')
            medal = ""
            row_class = ""
            if pos == 1:
                medal = '<span class="medal gold">1</span>'
                row_class = "row-first"
            elif pos == 2:
                medal = '<span class="medal silver">2</span>'
            elif pos == 3:
                medal = '<span class="medal bronze">3</span>'
            else:
                medal = f'<span class="medal plain">{pos}</span>'
            rows_html += f"""
            <tr class="{row_class}">
                <td>{medal}</td>
                <td><span class="driver-name">{nombre}</span><span class="driver-email">{email}</span></td>
                <td><span class="pts-big">{pts}</span></td>
                <td>{cambio}</td>
            </tr>"""
        ranking_acumulado_html = f"""
        <div class="table-wrapper">
        <table class="data-table leaderboard">
            <thead><tr><th>#</th><th>Participante</th><th>Puntos</th><th>Cambio</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>"""
    else:
        ranking_acumulado_html = '<p class="empty-msg">No hay datos disponibles.</p>'

    # ---- Rankings por carrera ----
    rankings_por_carrera_html = ""
    for i, ranking in enumerate(rankings_por_carrera):
        carrera = ranking["Carrera"].iloc[0]
        table_rows = ""
        for j, row in ranking.iterrows():
            pos = row['Posición']
            email = row['Dirección de correo electrónico']
            pts = row['Puntos']
            table_rows += f"<tr><td>{pos}</td><td>{email.split('@')[0]}<span class='driver-email'>{email}</span></td><td><span class='pts-chip'>{pts}</span></td></tr>"

        detalles_html = ""
        for j, row in ranking.iterrows():
            email = row["Dirección de correo electrónico"]
            detalles = row["Detalles"]
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

    # ---- Calendario ----
    cal_rows = ""
    for _, row in calendario_df.iterrows():
        jornada = row['Jornada']
        carrera = row['Carrera']
        fecha = row['Fecha']
        hora_l = row['Hora Local']
        hora_a = row['Hora Argentina']
        tachado = '<s>' in str(jornada)
        row_class = "cal-cancelled" if tachado else ""
        cal_rows += f"<tr class='{row_class}'><td class='cal-jornada'>{jornada}</td><td class='cal-carrera'>{carrera}</td><td>{fecha}</td><td>{hora_l}</td><td>{hora_a}</td></tr>"

    calendario_html = f"""
    <div class="table-wrapper">
    <table class="data-table cal-table">
        <thead><tr><th>Jornada</th><th>Gran Premio</th><th>Fecha</th><th>Hora Local</th><th>ARG (GMT-3)</th></tr></thead>
        <tbody>{cal_rows}</tbody>
    </table>
    </div>"""

    # ---- Radares ----
    radars_html = ""
    if radars_data:
        for carrera, b64 in radars_data:
            radars_html += f"""
            <div class="radar-block">
                <div class="radar-label">{carrera}</div>
                <img src="data:image/png;base64,{b64}" alt="Radar {carrera}" class="chart-img">
            </div>"""
    else:
        radars_html = '<p class="empty-msg">No hay suficientes datos para mostrar perfiles de aciertos.</p>'

    fecha_actual = datetime.now().strftime("%d/%m/%Y · %H:%M")
    carreras_procesadas = len(rankings_por_carrera)

    # ---- Imagen de barra si existe ----
    grafico_barras_html = f'<img src="data:image/png;base64,{grafico_barras}" alt="Puntos acumulados" class="chart-img">' if grafico_barras else '<p class="empty-msg">Sin datos.</p>'
    grafico_evolucion_html = f'<img src="data:image/png;base64,{grafico_evolucion}" alt="Evolución" class="chart-img">' if grafico_evolucion else '<p class="empty-msg">Sin datos.</p>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>F1 Predictions · 2026</title>
<link rel="icon" href="https://www.formula1.com/etc/designs/f1/img/favicon.ico" type="image/x-icon">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700;800&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
    --red: #E10600;
    --red-dim: #8a0300;
    --bg: #080808;
    --bg-2: #111111;
    --bg-3: #181818;
    --bg-4: #1F1F1F;
    --border: rgba(255,255,255,0.07);
    --border-bright: rgba(255,255,255,0.13);
    --text: #F0F0F0;
    --muted: #888888;
    --muted-2: #555555;
    --gold: #FFD700;
    --silver: #C0C0C0;
    --bronze: #CD7F32;
    --green: #22c55e;
    --danger: #ef4444;
    --font-display: 'Barlow Condensed', sans-serif;
    --font-body: 'Barlow', sans-serif;
}}

html {{ scroll-behavior: smooth; }}

body {{
    font-family: var(--font-body);
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    font-size: 15px;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
}}

/* ===== HEADER ===== */
.site-header {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: rgba(8,8,8,0.95);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
}}

.header-inner {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    gap: 16px;
}}

.header-brand {{
    display: flex;
    align-items: center;
    gap: 12px;
    flex-shrink: 0;
}}

.brand-stripe {{
    width: 4px;
    height: 32px;
    background: var(--red);
    border-radius: 2px;
}}

.brand-text {{
    font-family: var(--font-display);
    font-size: 1.25rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    line-height: 1.1;
    text-transform: uppercase;
}}

.brand-sub {{
    font-size: 0.7rem;
    color: var(--muted);
    font-weight: 400;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 1px;
}}

.header-meta {{
    font-size: 0.75rem;
    color: var(--muted);
    text-align: right;
    line-height: 1.4;
}}

.header-meta strong {{
    color: var(--red);
    font-family: var(--font-display);
    font-size: 1.1rem;
    font-weight: 700;
    display: block;
}}

/* ===== NAV TABS ===== */
.tab-nav {{
    background: var(--bg-2);
    border-bottom: 1px solid var(--border);
    overflow-x: auto;
    scrollbar-width: none;
}}
.tab-nav::-webkit-scrollbar {{ display: none; }}

.tab-nav-inner {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
    display: flex;
    gap: 0;
}}

.tab-btn {{
    font-family: var(--font-display);
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
    background: none;
    border: none;
    border-bottom: 3px solid transparent;
    padding: 14px 18px;
    cursor: pointer;
    white-space: nowrap;
    transition: color 0.2s, border-color 0.2s;
}}

.tab-btn:hover {{ color: var(--text); }}
.tab-btn.active {{ color: var(--text); border-bottom-color: var(--red); }}

/* ===== MAIN LAYOUT ===== */
.main {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 20px 80px;
}}

.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; animation: fadeIn 0.25s ease; }}

@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}

/* ===== SECTION HEADING ===== */
.section-heading {{
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    text-transform: uppercase;
    margin-bottom: 8px;
    line-height: 1;
}}

.section-heading span {{ color: var(--red); }}

.section-label {{
    font-family: var(--font-display);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 12px;
    margin-top: 4px;
}}

/* ===== TABLE ===== */
.table-wrapper {{
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid var(--border);
    background: var(--bg-2);
    -webkit-overflow-scrolling: touch;
}}

.data-table {{
    width: 100%;
    border-collapse: collapse;
    min-width: 480px;
}}

.data-table th {{
    font-family: var(--font-display);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    padding: 14px 16px;
    border-bottom: 1px solid var(--border);
    text-align: left;
    background: var(--bg-3);
    white-space: nowrap;
}}

.data-table td {{
    padding: 13px 16px;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
}}

.data-table tr:last-child td {{ border-bottom: none; }}
.data-table tr:hover td {{ background: rgba(255,255,255,0.025); }}
.data-table .row-first td {{ background: rgba(225,6,0,0.05); }}

/* ===== LEADERBOARD ESPECÍFICO ===== */
.leaderboard {{ min-width: 520px; }}

.medal {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    font-family: var(--font-display);
    font-weight: 800;
    font-size: 0.85rem;
}}
.medal.gold {{ background: rgba(255,215,0,0.15); color: var(--gold); border: 1px solid rgba(255,215,0,0.3); }}
.medal.silver {{ background: rgba(192,192,192,0.12); color: var(--silver); border: 1px solid rgba(192,192,192,0.25); }}
.medal.bronze {{ background: rgba(205,127,50,0.12); color: var(--bronze); border: 1px solid rgba(205,127,50,0.25); }}
.medal.plain {{ background: var(--bg-4); color: var(--muted); border: 1px solid var(--border); }}

.driver-name {{
    display: block;
    font-weight: 600;
    font-size: 0.92rem;
}}
.driver-email {{
    display: block;
    font-size: 0.76rem;
    color: var(--muted);
    margin-top: 1px;
}}

.pts-big {{
    font-family: var(--font-display);
    font-size: 1.35rem;
    font-weight: 800;
    color: var(--text);
}}

.pts-chip {{
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 700;
    background: var(--bg-4);
    padding: 3px 10px;
    border-radius: 6px;
    border: 1px solid var(--border);
}}

.pts-tag {{
    font-size: 0.7rem;
    color: var(--muted);
    font-weight: 400;
}}

.trend-up {{ color: var(--green); font-weight: 700; font-size: 0.85rem; }}
.trend-down {{ color: var(--danger); font-weight: 700; font-size: 0.85rem; }}
.trend-neutral {{ color: var(--muted-2); font-weight: 700; }}

/* ===== DIVIDER ===== */
.divider {{
    height: 1px;
    background: var(--border);
    margin: 28px 0;
}}

/* ===== CHART ===== */
.chart-block {{
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}}

.chart-title {{
    font-family: var(--font-display);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 16px;
}}

.chart-img {{
    width: 100%;
    height: auto;
    display: block;
    border-radius: 8px;
}}

/* ===== RACE ACCORDION ===== */
.race-block {{
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 10px;
    background: var(--bg-2);
}}

.race-header {{
    width: 100%;
    background: var(--bg-3);
    border: none;
    color: var(--text);
    padding: 16px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    transition: background 0.15s;
    gap: 12px;
}}

.race-header:hover {{ background: var(--bg-4); }}

.race-title-wrap {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.race-badge {{
    font-family: var(--font-display);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 1.5px;
    background: var(--red);
    color: #fff;
    padding: 3px 8px;
    border-radius: 5px;
    flex-shrink: 0;
}}

.race-title {{
    font-family: var(--font-display);
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

.toggle-icon {{
    font-size: 1.3rem;
    color: var(--muted);
    font-style: normal;
    transition: transform 0.2s;
    flex-shrink: 0;
    line-height: 1;
}}

.race-body {{
    display: none;
    padding: 20px;
    border-top: 1px solid var(--border);
}}

/* ===== DETAIL ACCORDION ===== */
.detail-row {{
    border: 1px solid var(--border);
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 8px;
}}

.detail-toggle {{
    width: 100%;
    background: var(--bg-4);
    border: none;
    color: var(--text);
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    cursor: pointer;
    font-size: 0.88rem;
    font-weight: 600;
    transition: background 0.15s;
    gap: 8px;
}}

.detail-toggle:hover {{ background: #262626; }}

.detail-body {{
    display: none;
    padding: 14px 16px;
    background: var(--bg-2);
    border-top: 1px solid var(--border);
}}

.detail-text {{
    font-size: 0.85rem;
    color: #CCCCCC;
    line-height: 1.7;
}}

/* ===== STATS ===== */
.stats-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    margin-bottom: 24px;
}}

.stat-card {{
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 16px;
    text-align: center;
}}

.stat-card.accent {{
    border-color: var(--red);
    background: rgba(225,6,0,0.06);
}}

.stat-num {{
    font-family: var(--font-display);
    font-size: 2.4rem;
    font-weight: 800;
    color: var(--text);
    line-height: 1;
    margin-bottom: 6px;
}}

.stat-desc {{
    font-size: 0.76rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: var(--font-display);
}}

.leader-banner {{
    background: linear-gradient(135deg, rgba(225,6,0,0.12), rgba(225,6,0,0.04));
    border: 1px solid rgba(225,6,0,0.25);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 28px;
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
}}

.leader-label {{
    font-family: var(--font-display);
    font-size: 0.68rem;
    letter-spacing: 3px;
    font-weight: 800;
    color: var(--red);
    text-transform: uppercase;
    flex-shrink: 0;
}}

.leader-name {{
    font-family: var(--font-display);
    font-size: 1.4rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.leader-email {{
    font-size: 0.8rem;
    color: var(--muted);
    margin-left: auto;
}}

/* ===== CALENDARIO ===== */
.cal-table {{ min-width: 560px; }}
.cal-jornada {{ font-family: var(--font-display); font-weight: 700; font-size: 0.85rem; color: var(--red); }}
.cal-carrera {{ font-family: var(--font-display); font-weight: 700; font-size: 0.95rem; letter-spacing: 0.5px; }}
.cal-cancelled td {{ opacity: 0.35; }}

/* ===== RADAR ===== */
.radar-block {{
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    text-align: center;
}}

.radar-label {{
    font-family: var(--font-display);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--red);
    margin-bottom: 16px;
}}

/* ===== EMPTY ===== */
.empty-msg {{
    color: var(--muted);
    font-size: 0.9rem;
    font-style: italic;
    padding: 24px 0;
}}

/* ===== FOOTER ===== */
.site-footer {{
    border-top: 1px solid var(--border);
    padding: 20px;
    text-align: center;
    font-size: 0.78rem;
    color: var(--muted-2);
}}

.footer-stripe {{
    width: 32px;
    height: 3px;
    background: var(--red);
    border-radius: 2px;
    margin: 0 auto 12px;
}}

/* ===== RESPONSIVE ===== */
@media (max-width: 640px) {{
    .header-inner {{ height: 56px; padding: 0 14px; }}
    .brand-text {{ font-size: 1rem; }}
    .main {{ padding: 20px 14px 60px; }}
    .section-heading {{ font-size: 1.5rem; }}
    .tab-btn {{ padding: 12px 12px; font-size: 0.78rem; letter-spacing: 1px; }}
    .stats-grid {{ grid-template-columns: 1fr 1fr; }}
    .leader-banner {{ gap: 10px; }}
    .leader-email {{ display: none; }}
    .race-header {{ padding: 14px 14px; }}
    .race-body {{ padding: 14px; }}
    .data-table th, .data-table td {{ padding: 11px 12px; }}
    .stat-num {{ font-size: 2rem; }}
}}
</style>
</head>
<body>

<header class="site-header">
    <div class="header-inner">
        <div class="header-brand">
            <div class="brand-stripe"></div>
            <div>
                <div class="brand-text">F1 Predictions</div>
                <div class="brand-sub">Torneo Familiar · 2026</div>
            </div>
        </div>
        <div class="header-meta">
            <strong>{carreras_procesadas}</strong>
            carrera{'s' if carreras_procesadas != 1 else ''} procesada{'s' if carreras_procesadas != 1 else ''}
        </div>
    </div>
</header>

<nav class="tab-nav">
    <div class="tab-nav-inner">
        <button class="tab-btn active" onclick="openTab(event,'panel-acumulado')">Acumulado</button>
        <button class="tab-btn" onclick="openTab(event,'panel-carreras')">Por Carrera</button>
        <button class="tab-btn" onclick="openTab(event,'panel-graficos')">Gráficos</button>
        <button class="tab-btn" onclick="openTab(event,'panel-stats')">Estadísticas</button>
        <button class="tab-btn" onclick="openTab(event,'panel-calendario')">Calendario</button>
    </div>
</nav>

<main class="main">

    <div id="panel-acumulado" class="tab-panel active">
        <h2 class="section-heading">Ranking <span>General</span></h2>
        <p class="section-label" style="margin-bottom:20px;">Puntos acumulados · Todas las carreras</p>
        {ranking_acumulado_html}
        <div class="divider"></div>
        <div class="chart-block">
            <div class="chart-title">Distribución de puntos</div>
            {grafico_barras_html}
        </div>
    </div>

    <div id="panel-carreras" class="tab-panel">
        <h2 class="section-heading">Rankings <span>por Carrera</span></h2>
        <p class="section-label" style="margin-bottom:20px;">Seleccioná una carrera para ver el detalle</p>
        {rankings_por_carrera_html}
    </div>

    <div id="panel-graficos" class="tab-panel">
        <h2 class="section-heading">Gráficos <span>&amp; Datos</span></h2>
        <p class="section-label" style="margin-bottom:20px;">Visualizaciones de la temporada</p>
        <div class="chart-block">
            <div class="chart-title">Evolución de puntos · Top 5</div>
            {grafico_evolucion_html}
        </div>
        <div class="section-label" style="margin-top:32px;">Perfil de aciertos por carrera · Radar Top 8</div>
        {radars_html}
    </div>

    <div id="panel-stats" class="tab-panel">
        <h2 class="section-heading">Esta<span>dísticas</span></h2>
        <p class="section-label" style="margin-bottom:20px;">Resumen general de la temporada</p>
        {stats_adicionales}
    </div>

    <div id="panel-calendario" class="tab-panel">
        <h2 class="section-heading">Calen<span>dario</span></h2>
        <p class="section-label" style="margin-bottom:20px;">F1 World Championship 2026 · Horarios ARG (GMT−3)</p>
        {calendario_html}
    </div>

</main>

<footer class="site-footer">
    <div class="footer-stripe"></div>
    Generado automáticamente · {fecha_actual}
</footer>

<script>
function openTab(evt, panelId) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(panelId).classList.add('active');
    evt.currentTarget.classList.add('active');
}}

function toggleDetail(id) {{
    const el = document.getElementById(id);
    const iconId = 'icon-' + id;
    const icon = document.getElementById(iconId);
    const isOpen = el.style.display === 'block';
    el.style.display = isOpen ? 'none' : 'block';
    if (icon) icon.textContent = isOpen ? '＋' : '－';
}}
</script>
</body>
</html>"""

# =========================
# MAIN
# =========================
def main():
    if not os.path.exists(CARPETA_RESPUESTAS):
        print(f"Carpeta '{CARPETA_RESPUESTAS}' no existe. Créala y agregá los CSV.")
        return

    with open(ARCHIVO_RESULTADOS, 'r') as f:
        resultados_por_carrera = json.load(f)

    rankings_por_carrera = []
    all_rankings = pd.DataFrame()
    all_dfs = []

    archivos = sorted(os.listdir(CARPETA_RESPUESTAS))
    for archivo in archivos:
        if archivo.endswith(".csv"):
            nombre_carrera = archivo.replace("respuestas_", "").replace(".csv", "").capitalize()
            if nombre_carrera in resultados_por_carrera and resultados_por_carrera[nombre_carrera].get("resultado_carrera"):
                archivo_path = os.path.join(CARPETA_RESPUESTAS, archivo)
                ranking, df = procesar_carrera(nombre_carrera, archivo_path, resultados_por_carrera[nombre_carrera])
                rankings_por_carrera.append(ranking)
                all_rankings = pd.concat([all_rankings, ranking.drop(columns=["Detalles"])])
                all_dfs.append(df)
            else:
                print(f"Advertencia: No hay resultados reales completos para {nombre_carrera}")

    if not all_rankings.empty:
        ranking_acumulado = (
            all_rankings.groupby("Dirección de correo electrónico", as_index=False)["Puntos"]
            .sum()
            .sort_values("Puntos", ascending=False)
            .reset_index(drop=True)
        )
        ranking_acumulado["Posición"] = ranking_acumulado.index + 1
        ranking_acumulado = ranking_acumulado[["Posición", "Dirección de correo electrónico", "Puntos"]]
        ranking_acumulado = calcular_cambios_posiciones(all_rankings, ranking_acumulado)
    else:
        ranking_acumulado = pd.DataFrame(columns=["Posición", "Dirección de correo electrónico", "Puntos", "Cambio"])

    grafico_barras = generar_grafico_barras_acumulado(ranking_acumulado)
    grafico_evolucion = generar_grafico_evolucion(all_rankings)
    radars_data = generar_radar_por_carrera(all_dfs, top_n=8)
    stats_adicionales = generar_estadisticas_adicionales(all_dfs, ranking_acumulado)

    html_content = generar_html(
        rankings_por_carrera, ranking_acumulado,
        grafico_barras, grafico_evolucion, radars_data,
        stats_adicionales
    )

    with open("ranking_f1.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("🏁 HTML generado: ranking_f1.html")
    print("   Abrilo en cualquier navegador o celular.")

if __name__ == "__main__":
    main()