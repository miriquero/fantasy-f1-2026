import pandas as pd
import os
import json
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import base64
from io import BytesIO
from datetime import datetime
import numpy as np
import re

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

# Fechas ISO para el countdown (año-mes-día hora:minuto en hora argentina GMT-3)
CALENDARIO = [
    {"Jornada": "R01", "Carrera": "AUSTRALIA",      "Fecha": "8 MAR",   "Hora Local": "15:00", "Hora Argentina": "01:00",              "FechaISO": "2026-03-08T01:00:00"},
    {"Jornada": "R02", "Carrera": "CHINA",           "Fecha": "15 MAR",  "Hora Local": "15:00", "Hora Argentina": "04:00",              "FechaISO": "2026-03-15T04:00:00"},
    {"Jornada": "R03", "Carrera": "JAPON",           "Fecha": "29 MAR",  "Hora Local": "14:00", "Hora Argentina": "02:00",              "FechaISO": "2026-03-29T02:00:00"},
    {"Jornada": "<s>R04</s>", "Carrera": "<s>BAHREIN</s>",        "Fecha": "<s>12 ABR</s>", "Hora Local": "<s>18:00</s>", "Hora Argentina": "<s>12:00</s>", "FechaISO": None},
    {"Jornada": "<s>R05</s>", "Carrera": "<s>ARABIA SAUDITA</s>", "Fecha": "<s>19 ABR</s>", "Hora Local": "<s>20:00</s>", "Hora Argentina": "<s>14:00</s>", "FechaISO": None},
    {"Jornada": "R06", "Carrera": "MIAMI",          "Fecha": "03 MAY",  "Hora Local": "16:00", "Hora Argentina": "17:00",              "FechaISO": "2026-05-03T17:00:00"},
    {"Jornada": "R07", "Carrera": "CANADA",         "Fecha": "24 MAY",  "Hora Local": "16:00", "Hora Argentina": "17:00",              "FechaISO": "2026-05-24T17:00:00"},
    {"Jornada": "R08", "Carrera": "MÓNACO",         "Fecha": "07 JUN",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-06-07T10:00:00"},
    {"Jornada": "R09", "Carrera": "BARCELONA",      "Fecha": "14 JUN",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-06-14T10:00:00"},
    {"Jornada": "R10", "Carrera": "AUSTRIA",        "Fecha": "28 JUN",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-06-28T10:00:00"},
    {"Jornada": "R11", "Carrera": "GRAN BRETAÑA",   "Fecha": "05 JUL",  "Hora Local": "15:00", "Hora Argentina": "11:00",              "FechaISO": "2026-07-05T11:00:00"},
    {"Jornada": "R12", "Carrera": "BÉLGICA",        "Fecha": "19 JUL",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-07-19T10:00:00"},
    {"Jornada": "R13", "Carrera": "HUNGRÍA",        "Fecha": "26 JUL",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-07-26T10:00:00"},
    {"Jornada": "R14", "Carrera": "PAÍSES BAJOS",   "Fecha": "23 AGO",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-08-23T10:00:00"},
    {"Jornada": "R15", "Carrera": "ITALIA",         "Fecha": "06 SEP",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-09-06T10:00:00"},
    {"Jornada": "R16", "Carrera": "MADRID",         "Fecha": "13 SEP",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-09-13T10:00:00"},
    {"Jornada": "R17", "Carrera": "AZERBAIYN",     "Fecha": "26 SEP",  "Hora Local": "15:00", "Hora Argentina": "08:00",              "FechaISO": "2026-09-26T08:00:00"},
    {"Jornada": "R18", "Carrera": "SINGAPUR",       "Fecha": "11 OCT",  "Hora Local": "20:00", "Hora Argentina": "09:00",              "FechaISO": "2026-10-11T09:00:00"},
    {"Jornada": "R19", "Carrera": "AUSTIN",         "Fecha": "25 OCT",  "Hora Local": "15:00", "Hora Argentina": "17:00",              "FechaISO": "2026-10-25T17:00:00"},
    {"Jornada": "R20", "Carrera": "MEXICO",         "Fecha": "01 NOV",  "Hora Local": "14:00", "Hora Argentina": "17:00",              "FechaISO": "2026-11-01T17:00:00"},
    {"Jornada": "R21", "Carrera": "BRASIL",         "Fecha": "08 NOV",  "Hora Local": "14:00", "Hora Argentina": "14:00",              "FechaISO": "2026-11-08T14:00:00"},
    {"Jornada": "R22", "Carrera": "LAS VEGAS",      "Fecha": "21 NOV",  "Hora Local": "20:00", "Hora Argentina": "01:00 (Domingo 22)", "FechaISO": "2026-11-22T01:00:00"},
    {"Jornada": "R23", "Carrera": "QATAR",          "Fecha": "29 NOV",  "Hora Local": "19:00", "Hora Argentina": "13:00",              "FechaISO": "2026-11-29T13:00:00"},
    {"Jornada": "R24", "Carrera": "ABU DHABI",      "Fecha": "06 DIC",  "Hora Local": "17:00", "Hora Argentina": "10:00",              "FechaISO": "2026-12-06T10:00:00"},
]

COLORES_PARTICIPANTES = ['#E10600','#00C8FF','#FFD700','#C77DFF','#39FF14','#FF6B35','#00E5CC','#FF69B4']

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
def calcular_puntos_y_detalles(row: pd.Series, posiciones_reales: Dict[str, int],
                                vuelta_rapida_real: str, colapinto_real: int) -> Tuple[int, str]:
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
        "Sexto": 6, "Séptimo": 7, "Septimo": 7, "Octavo": 8, "Noveno": 9,
        "Décimo": 10, "Decimo": 10, "Undécimo": 11, "Duodécimo": 12,
        "Décimo Segundo": 12, "Décimo Tercer": 13, "Décimo Tercero": 13,
        "Décimo Cuarto": 14, "Décimo Quinto": 15, "Décimo Sexto": 16,
        "Décimo Séptimo": 17, "Décimo Octavo": 18, "Décimo Noveno": 19, "Vigésimo": 20,
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
        lambda row: pd.Series(calcular_puntos_y_detalles(
            row, posiciones_reales, vuelta_rapida_real, colapinto_real)),
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
    prev_rankings = all_rankings[all_rankings['Carrera'] != carreras[-1]]
    if prev_rankings.empty:
        acum_prev = pd.Series()
    else:
        acum_prev = prev_rankings.groupby("Dirección de correo electrónico")["Puntos"].sum()\
            .sort_values(ascending=False).reset_index()
        acum_prev["Posición"] = acum_prev.index + 1
        acum_prev = acum_prev.set_index('Dirección de correo electrónico')['Posición']

    cambios = {}
    for email in ranking_acumulado['Dirección de correo electrónico']:
        pos_actual = ranking_acumulado[
            ranking_acumulado['Dirección de correo electrónico'] == email]['Posición'].values[0]
        pos_prev = acum_prev.get(email, float('inf'))
        diff = pos_prev - pos_actual
        if diff > 0:
            cambios[email] = f'<span class="trend-up">▲{int(diff)}</span>'
        elif diff < 0:
            cambios[email] = f'<span class="trend-down">▼{int(-diff)}</span>'
        else:
            cambios[email] = '<span class="trend-neutral">—</span>'

    ranking_acumulado['Cambio'] = ranking_acumulado['Dirección de correo electrónico'].map(cambios)
    return ranking_acumulado

# =========================
# HISTORIAL DE POSICIONES POR CARRERA (para bump chart y perfiles)
# =========================
def calcular_historial_posiciones(all_rankings: pd.DataFrame) -> pd.DataFrame:
    """Devuelve DataFrame con posición acumulada de cada participante después de cada carrera."""
    if all_rankings.empty:
        return pd.DataFrame()
    carreras = sorted(all_rankings['Carrera'].unique())
    rows = []
    for i, carrera in enumerate(carreras):
        subset = all_rankings[all_rankings['Carrera'].isin(carreras[:i+1])]
        acum = subset.groupby("Dirección de correo electrónico")["Puntos"].sum()\
            .sort_values(ascending=False).reset_index()
        acum["Posición"] = acum.index + 1
        acum["Carrera"] = carrera
        rows.append(acum)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

# =========================
# GRÁFICO DE BARRAS ACUMULADO
# =========================
def generar_grafico_barras_acumulado(ranking_acumulado: pd.DataFrame) -> str:
    if ranking_acumulado.empty:
        return ""

    plt.rcParams['font.family'] = 'DejaVu Sans'
    fig, ax = plt.subplots(figsize=(10, max(4, len(ranking_acumulado) * 0.45 + 1)))

    colors = ['#E10600' if i == 0 else '#2A2A2A' for i in range(len(ranking_acumulado))]
    bars = ax.barh(ranking_acumulado["Dirección de correo electrónico"],
                   ranking_acumulado["Puntos"], color=colors, height=0.65, edgecolor='none')

    for bar, pts in zip(bars, ranking_acumulado["Puntos"]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{pts}', va='center', ha='left', color='#FFFFFF', fontsize=9, fontweight='bold')

    ax.set_title('Puntos acumulados', color='#FFFFFF', fontsize=13, pad=15, loc='left', fontweight='bold')
    ax.invert_yaxis()
    ax.tick_params(colors='#AAAAAA', labelsize=9)
    ax.set_facecolor('#0D0D0D')
    fig.patch.set_facecolor('#0D0D0D')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333333')
    ax.spines['left'].set_visible(False)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True, color='#1E1E1E', linewidth=0.8)

    plt.tight_layout(pad=1.5)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=False, dpi=130)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

# =========================
# GRÁFICO EVOLUCIÓN LÍNEAS
# =========================
def generar_grafico_evolucion(all_rankings: pd.DataFrame, top_n=5) -> str:
    if all_rankings.empty:
        return ""

    pivot = all_rankings.pivot_table(
        index="Dirección de correo electrónico", columns="Carrera",
        values="Puntos", fill_value=0).cumsum(axis=1)
    top_emails = pivot.iloc[:, -1].nlargest(top_n).index
    carreras_ordenadas = sorted(pivot.columns)
    pivot = pivot[carreras_ordenadas]

    fig, ax = plt.subplots(figsize=(12, 6))
    for i, email in enumerate(top_emails):
        c = COLORES_PARTICIPANTES[i % len(COLORES_PARTICIPANTES)]
        ax.plot(pivot.columns, pivot.loc[email], marker='o', linewidth=2.5,
                markersize=7, label=email.split('@')[0], color=c,
                markerfacecolor='#0D0D0D', markeredgecolor=c, markeredgewidth=2)

    ax.set_title('Evolución de puntos · Top 5', color='#FFFFFF', fontsize=13,
                 pad=15, loc='left', fontweight='bold')
    ax.set_ylabel('Puntos acumulados', color='#888888', fontsize=9)
    ax.legend(loc='upper left', frameon=False, labelcolor='#DDDDDD', fontsize=9)
    ax.grid(True, color='#1E1E1E', linewidth=0.8)
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

# =========================
# BUMP CHART — HISTORIAL DE POSICIONES
# =========================
def generar_bump_chart(all_rankings: pd.DataFrame) -> str:
    """Gráfico de líneas que muestra el puesto (no puntos) después de cada carrera."""
    if all_rankings.empty:
        return ""

    historial = calcular_historial_posiciones(all_rankings)
    if historial.empty:
        return ""

    carreras = sorted(historial['Carrera'].unique())
    participantes = historial.groupby("Dirección de correo electrónico")["Puntos"]\
        .sum().sort_values(ascending=False).index.tolist()

    n_carr = len(carreras)
    n_part = len(participantes)
    fig_h = max(5, n_part * 0.6 + 1.5)
    fig, ax = plt.subplots(figsize=(max(8, n_carr * 1.4), fig_h))

    x_pos = list(range(n_carr))

    for i, email in enumerate(participantes):
        color = COLORES_PARTICIPANTES[i % len(COLORES_PARTICIPANTES)]
        nombre = email.split('@')[0]
        data = historial[historial["Dirección de correo electrónico"] == email]
        data = data.set_index("Carrera").reindex(carreras)
        ys = data["Posición"].tolist()

        # línea suavizada con segmentos
        ax.plot(x_pos, ys, color=color, linewidth=2.5, zorder=2,
                solid_capstyle='round', solid_joinstyle='round')

        # puntos en cada carrera
        for xi, yi in enumerate(ys):
            if pd.isna(yi):
                continue
            ax.scatter(xi, yi, s=70, color=color, zorder=3,
                       edgecolors='#0D0D0D', linewidths=1.5)

        # etiqueta al inicio y al final
        if not pd.isna(ys[0]):
            ax.text(-0.15, ys[0], nombre, ha='right', va='center',
                    color=color, fontsize=8, fontweight='bold')
        last_valid = next((ys[-(j+1)] for j in range(len(ys)) if not pd.isna(ys[-(j+1)])), None)
        if last_valid is not None:
            ax.text(n_carr - 0.85, last_valid, f'P{int(last_valid)}',
                    ha='left', va='center', color=color, fontsize=8, fontweight='bold')

    ax.set_xticks(x_pos)
    ax.set_xticklabels([c[:3] for c in carreras], color='#AAAAAA', fontsize=8)
    ax.set_yticks(range(1, n_part + 1))
    ax.set_yticklabels([f'P{p}' for p in range(1, n_part + 1)], color='#AAAAAA', fontsize=8)
    ax.invert_yaxis()
    ax.set_ylim(n_part + 0.5, 0.5)
    ax.set_xlim(-1.5, n_carr + 0.3)
    ax.set_title('Historial de posiciones · Bump chart', color='#FFFFFF',
                 fontsize=13, pad=15, loc='left', fontweight='bold')
    ax.set_facecolor('#0D0D0D')
    fig.patch.set_facecolor('#0D0D0D')
    ax.grid(True, color='#1E1E1E', linewidth=0.6, axis='both')
    for spine in ax.spines.values():
        spine.set_color('#333333')
    ax.tick_params(colors='#555555')

    plt.tight_layout(pad=1.5)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=False, dpi=140)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

# =========================
# RADAR POR CARRERA
# =========================
def generar_radar_por_carrera(all_dfs: List[pd.DataFrame], top_n=5) -> List[Tuple[str, str]]:
    if not all_dfs:
        return []

    df_all = pd.concat(all_dfs)
    categorias = ['Exactos', 'Cercanos', 'Top10', 'V.Rápida', 'Colapinto']

    def breakdown_puntos(row):
        exactos  = sum(1 for d in row['Detalles'].split('<br>') if 'Exacto' in d) * 10
        cercanos = sum(1 for d in row['Detalles'].split('<br>') if 'Diff 1' in d) * 5
        top10    = sum(1 for d in row['Detalles'].split('<br>') if 'En top 10' in d) * 1
        vr  = 10 if 'Vuelta rápida' in row['Detalles'] else 0
        col = 10 if 'Colapinto: EXACTO' in row['Detalles'] else (
              5  if 'Colapinto: diferencia de 1' in row['Detalles'] else 0)
        return pd.Series({'Exactos': exactos, 'Cercanos': cercanos,
                          'Top10': top10, 'VueltaRapida': vr, 'Colapinto': col})

    breakdowns = df_all.apply(breakdown_puntos, axis=1)
    df_with_break = pd.concat(
        [df_all[['Carrera', 'Dirección de correo electrónico', 'Puntos']], breakdowns], axis=1)

    radars = []
    for carrera, group in df_with_break.groupby('Carrera'):
        if group.empty:
            continue
        top_group = group.nlargest(top_n, 'Puntos').copy()
        if top_group.empty:
            continue

        max_por_cat = {'Exactos': 100, 'Cercanos': 50, 'Top10': 10, 'VueltaRapida': 10, 'Colapinto': 10}
        for cat in ['Exactos', 'Cercanos', 'Top10', 'VueltaRapida', 'Colapinto']:
            top_group[cat] = top_group[cat] / max_por_cat[cat] * 100

        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2*np.pi, len(categorias), endpoint=False).tolist()
        angles += angles[:1]
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        for i, (_, row) in enumerate(top_group.iterrows()):
            c = COLORES_PARTICIPANTES[i % len(COLORES_PARTICIPANTES)]
            values = row[['Exactos', 'Cercanos', 'Top10', 'VueltaRapida', 'Colapinto']].tolist()
            values += values[:1]
            ax.plot(angles, values, linewidth=2, linestyle='solid',
                    label=f"{row['Dirección de correo electrónico'].split('@')[0]} ({int(row['Puntos'])} pts)",
                    color=c)
            ax.fill(angles, values, color=c, alpha=0.12)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categorias, fontsize=10, color='#CCCCCC')
        ax.set_ylim(0, 100)
        ax.set_yticklabels([])
        ax.grid(color='#222222', linewidth=0.8)
        ax.set_facecolor('#0D0D0D')
        fig.patch.set_facecolor('#0D0D0D')
        ax.spines['polar'].set_color('#333333')
        ax.set_title(f'Perfil de aciertos · {carrera}\nTop {min(top_n, len(top_group))}',
                     color='#FFFFFF', fontsize=12, pad=25, fontweight='bold')
        ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.12),
                  labelcolor='#CCCCCC', frameon=False, fontsize=8)

        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches='tight', transparent=False, dpi=130)
        buf.seek(0)
        img_b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        radars.append((carrera, img_b64))

    return radars

# =========================
# GRÁFICO MINI PARA PERFIL (sparkline de puntos por carrera)
# =========================
def generar_sparkline_perfil(email: str, all_rankings: pd.DataFrame) -> str:
    data = all_rankings[all_rankings["Dirección de correo electrónico"] == email]
    if data.empty:
        return ""
    carreras = sorted(data['Carrera'].unique())
    pts = [data[data['Carrera'] == c]['Puntos'].values[0] for c in carreras]

    fig, ax = plt.subplots(figsize=(5, 1.8))
    color = '#E10600'
    ax.fill_between(range(len(pts)), pts, alpha=0.18, color=color)
    ax.plot(range(len(pts)), pts, color=color, linewidth=2.5, marker='o',
            markersize=6, markerfacecolor='#0D0D0D', markeredgecolor=color, markeredgewidth=2)
    for xi, yi in enumerate(pts):
        ax.text(xi, yi + max(pts)*0.05, str(yi), ha='center', va='bottom',
                color='#FFFFFF', fontsize=7, fontweight='bold')
    ax.set_xticks(range(len(carreras)))
    ax.set_xticklabels([c[:3] for c in carreras], color='#888888', fontsize=7)
    ax.set_yticks([])
    ax.set_facecolor('#0D0D0D')
    fig.patch.set_facecolor('#0D0D0D')
    for spine in ax.spines.values():
        spine.set_visible(False)
    plt.tight_layout(pad=0.3)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=False, dpi=120)
    buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

# =========================
# GENERAR PERFILES POR PARTICIPANTE
# =========================
def generar_perfiles_html(all_rankings: pd.DataFrame, all_dfs: List[pd.DataFrame],
                           ranking_acumulado: pd.DataFrame) -> str:
    if all_rankings.empty or ranking_acumulado.empty:
        return '<p class="empty-msg">Sin datos disponibles.</p>'

    historial_pos = calcular_historial_posiciones(all_rankings)
    df_all = pd.concat(all_dfs) if all_dfs else pd.DataFrame()
    carreras_lista = sorted(all_rankings['Carrera'].unique())
    total_carreras = len(carreras_lista)

    perfiles_html = ""
    for idx, (_, acum_row) in enumerate(ranking_acumulado.iterrows()):
        email    = acum_row['Dirección de correo electrónico']
        nombre   = email.split('@')[0]
        pos_gral = int(acum_row['Posición'])
        pts_tot  = int(acum_row['Puntos'])
        color    = COLORES_PARTICIPANTES[idx % len(COLORES_PARTICIPANTES)]

        # Estadísticas individuales
        data_part = all_rankings[all_rankings["Dirección de correo electrónico"] == email]
        pts_por_carrera = [data_part[data_part['Carrera'] == c]['Puntos'].values[0]
                           if c in data_part['Carrera'].values else 0
                           for c in carreras_lista]
        mejor_carrera_idx = int(np.argmax(pts_por_carrera)) if pts_por_carrera else 0
        mejor_carrera     = carreras_lista[mejor_carrera_idx] if carreras_lista else "—"
        mejor_pts         = max(pts_por_carrera) if pts_por_carrera else 0
        promedio          = round(sum(pts_por_carrera) / len(pts_por_carrera), 1) if pts_por_carrera else 0

        # Racha: máxima cantidad de carreras consecutivas mejorando posición
        pos_hist = []
        if not historial_pos.empty:
            for c in carreras_lista:
                row_h = historial_pos[(historial_pos["Dirección de correo electrónico"] == email) &
                                      (historial_pos["Carrera"] == c)]
                pos_hist.append(int(row_h["Posición"].values[0]) if not row_h.empty else None)

        racha_max = 0
        racha_actual = 0
        for k in range(1, len(pos_hist)):
            if pos_hist[k] is not None and pos_hist[k-1] is not None:
                if pos_hist[k] < pos_hist[k-1]:
                    racha_actual += 1
                    racha_max = max(racha_max, racha_actual)
                else:
                    racha_actual = 0

        # Exactos totales
        exactos_total = 0
        if not df_all.empty:
            part_df = df_all[df_all["Dirección de correo electrónico"] == email]
            for _, r in part_df.iterrows():
                exactos_total += sum(1 for d in r['Detalles'].split('<br>') if 'Exacto' in d)

        # Sparkline
        spark_b64 = generar_sparkline_perfil(email, all_rankings)
        spark_html = (f'<img src="data:image/png;base64,{spark_b64}" '
                      f'alt="Puntos por carrera" class="spark-img">') if spark_b64 else ""

        # Historial de posición por carrera (mini tabla)
        hist_rows = ""
        for c in carreras_lista:
            row_h = historial_pos[(historial_pos["Dirección de correo electrónico"] == email) &
                                  (historial_pos["Carrera"] == c)]
            pos_c  = int(row_h["Posición"].values[0])  if not row_h.empty else "—"
            pts_c  = int(data_part[data_part['Carrera'] == c]['Puntos'].values[0]) \
                     if c in data_part['Carrera'].values else "—"
            medal_c = "🥇" if pos_c == 1 else ("🥈" if pos_c == 2 else ("🥉" if pos_c == 3 else ""))
            hist_rows += (f"<tr><td class='cal-carrera'>{c}</td>"
                          f"<td>{medal_c} P{pos_c}</td>"
                          f"<td><span class='pts-chip'>{pts_c}</span></td></tr>")

        medal_str = ""
        if pos_gral == 1:   medal_str = '<span class="medal gold">1</span>'
        elif pos_gral == 2: medal_str = '<span class="medal silver">2</span>'
        elif pos_gral == 3: medal_str = '<span class="medal bronze">3</span>'
        else:               medal_str = f'<span class="medal plain">{pos_gral}</span>'

        perfiles_html += f"""
        <div class="perfil-card" id="perfil-{idx}">
            <div class="perfil-header" style="border-left: 4px solid {color};">
                <div class="perfil-avatar" style="background: {color}22; color: {color}; border: 1px solid {color}44;">
                    {nombre[:2].upper()}
                </div>
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
                <div class="perfil-stat">
                    <div class="perfil-stat-num">{promedio}</div>
                    <div class="perfil-stat-label">Prom. por carrera</div>
                </div>
                <div class="perfil-stat">
                    <div class="perfil-stat-num">{mejor_pts}</div>
                    <div class="perfil-stat-label">Mejor carrera</div>
                </div>
                <div class="perfil-stat">
                    <div class="perfil-stat-num">{exactos_total}</div>
                    <div class="perfil-stat-label">Predicciones exactas</div>
                </div>
                <div class="perfil-stat">
                    <div class="perfil-stat-num">{racha_max}</div>
                    <div class="perfil-stat-label">Racha mejorando</div>
                </div>
            </div>

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
                            <thead><tr><th>Gran Premio</th><th>Posición general</th><th>Puntos</th></tr></thead>
                            <tbody>{hist_rows}</tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        """

    return perfiles_html

# =========================
# ESTADÍSTICAS ADICIONALES
# =========================
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

    maximos_por_carrera = df_all.groupby('Carrera')['Puntos'].max()
    maximos_rows = "".join([
        f'<tr><td class="stat-label">{c}</td>'
        f'<td class="stat-value">{p} <span class="pts-tag">pts</span></td></tr>'
        for c, p in maximos_por_carrera.items()
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
# PRÓXIMA CARRERA PARA COUNTDOWN
# =========================
def obtener_proxima_carrera() -> Tuple[str, str]:
    """Devuelve (nombre_carrera, fechaISO) de la próxima carrera no cancelada."""
    ahora = datetime.now()
    for item in CALENDARIO:
        if item.get("FechaISO") is None:
            continue
        try:
            fecha = datetime.fromisoformat(item["FechaISO"])
            if fecha > ahora:
                return item["Carrera"], item["FechaISO"]
        except:
            continue
    return "FIN DE TEMPORADA", ""

# =========================
# GENERAR HTML COMPLETO
# =========================
def generar_html(rankings_por_carrera: List[pd.DataFrame],
                 ranking_acumulado: pd.DataFrame,
                 grafico_barras: str, grafico_evolucion: str,
                 bump_chart: str,
                 radars_data: List[Tuple[str, str]],
                 stats_adicionales: str,
                 perfiles_html: str) -> str:

    calendario_df = pd.DataFrame(CALENDARIO)
    proxima_carrera, proxima_iso = obtener_proxima_carrera()

    # ---- Ranking acumulado ----
    if not ranking_acumulado.empty:
        rows_html = ""
        for _, row in ranking_acumulado.iterrows():
            pos    = row['Posición']
            email  = row['Dirección de correo electrónico']
            nombre = email.split('@')[0]
            pts    = row['Puntos']
            cambio = row.get('Cambio', '—')
            if pos == 1:   medal = '<span class="medal gold">1</span>'; rc = "row-first"
            elif pos == 2: medal = '<span class="medal silver">2</span>'; rc = ""
            elif pos == 3: medal = '<span class="medal bronze">3</span>'; rc = ""
            else:          medal = f'<span class="medal plain">{pos}</span>'; rc = ""
            rows_html += f"""
            <tr class="{rc}" onclick="irPerfil({int(pos)-1})" style="cursor:pointer;" title="Ver perfil de {nombre}">
                <td>{medal}</td>
                <td><span class="driver-name">{nombre}</span><span class="driver-email">{email}</span></td>
                <td><span class="pts-big">{pts}</span></td>
                <td>{cambio}</td>
            </tr>"""
        ranking_acumulado_html = f"""
        <p class="section-label" style="margin-bottom:8px; color:var(--muted);">
            Hacé click en cualquier fila para ver el perfil del participante</p>
        <div class="table-wrapper">
        <table class="data-table leaderboard">
            <thead><tr><th>#</th><th>Participante</th><th>Puntos</th><th>Cambio</th></tr></thead>
            <tbody>{rows_html}</tbody>
        </table></div>"""
    else:
        ranking_acumulado_html = '<p class="empty-msg">No hay datos disponibles.</p>'

    # ---- Rankings por carrera ----
    rankings_por_carrera_html = ""
    for i, ranking in enumerate(rankings_por_carrera):
        carrera = ranking["Carrera"].iloc[0]
        table_rows = ""
        for j, row in ranking.iterrows():
            email = row['Dirección de correo electrónico']
            pts   = row['Puntos']
            table_rows += (f"<tr><td>{row['Posición']}</td>"
                           f"<td>{email.split('@')[0]}<span class='driver-email'>{email}</span></td>"
                           f"<td><span class='pts-chip'>{pts}</span></td></tr>")
        detalles_html = ""
        for j, row in ranking.iterrows():
            email   = row["Dirección de correo electrónico"]
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
        tachado   = '<s>' in str(row['Jornada'])
        rc        = "cal-cancelled" if tachado else ""
        cal_rows += (f"<tr class='{rc}'>"
                     f"<td class='cal-jornada'>{row['Jornada']}</td>"
                     f"<td class='cal-carrera'>{row['Carrera']}</td>"
                     f"<td>{row['Fecha']}</td>"
                     f"<td>{row['Hora Local']}</td>"
                     f"<td>{row['Hora Argentina']}</td></tr>")
    calendario_html = f"""
    <div class="table-wrapper">
    <table class="data-table cal-table">
        <thead><tr><th>Jornada</th><th>Gran Premio</th><th>Fecha</th><th>Hora Local</th><th>ARG (GMT-3)</th></tr></thead>
        <tbody>{cal_rows}</tbody>
    </table></div>"""

    # ---- Radares ----
    radars_html = ""
    if radars_data:
        for c, b64 in radars_data:
            radars_html += f"""
            <div class="radar-block">
                <div class="radar-label">{c}</div>
                <img src="data:image/png;base64,{b64}" alt="Radar {c}" class="chart-img">
            </div>"""
    else:
        radars_html = '<p class="empty-msg">No hay suficientes datos.</p>'

    # ---- Bump chart ----
    bump_html = (f'<img src="data:image/png;base64,{bump_chart}" '
                 f'alt="Historial posiciones" class="chart-img">') if bump_chart else \
                '<p class="empty-msg">Se necesitan al menos 2 carreras.</p>'

    # ---- Imagen barras / evolución ----
    graf_barras_html = (f'<img src="data:image/png;base64,{grafico_barras}" '
                        f'alt="Puntos acumulados" class="chart-img">') if grafico_barras else \
                       '<p class="empty-msg">Sin datos.</p>'
    graf_evol_html   = (f'<img src="data:image/png;base64,{grafico_evolucion}" '
                        f'alt="Evolución" class="chart-img">') if grafico_evolucion else \
                       '<p class="empty-msg">Sin datos.</p>'

    fecha_actual       = datetime.now().strftime("%d/%m/%Y · %H:%M")
    carreras_procesadas = len(rankings_por_carrera)

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
    --red: #E10600; --red-dim: #8a0300;
    --bg: #080808; --bg-2: #111111; --bg-3: #181818; --bg-4: #1F1F1F;
    --border: rgba(255,255,255,0.07); --border-bright: rgba(255,255,255,0.13);
    --text: #F0F0F0; --muted: #888888; --muted-2: #555555;
    --gold: #FFD700; --silver: #C0C0C0; --bronze: #CD7F32;
    --green: #22c55e; --danger: #ef4444;
    --font-display: 'Barlow Condensed', sans-serif;
    --font-body: 'Barlow', sans-serif;
}}
html {{ scroll-behavior: smooth; }}
body {{ font-family: var(--font-body); background: var(--bg); color: var(--text);
        min-height: 100vh; font-size: 15px; line-height: 1.55;
        -webkit-font-smoothing: antialiased; }}

/* HEADER */
.site-header {{ position: sticky; top: 0; z-index: 100;
    background: rgba(8,8,8,0.95); backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); }}
.header-inner {{ max-width: 1200px; margin: 0 auto; padding: 0 20px;
    display: flex; align-items: center; justify-content: space-between;
    min-height: 64px; gap: 16px; flex-wrap: wrap; padding-top: 6px; padding-bottom: 6px; }}
.header-brand {{ display: flex; align-items: center; gap: 12px; flex-shrink: 0; }}
.brand-stripe {{ width: 4px; height: 32px; background: var(--red); border-radius: 2px; }}
.brand-text {{ font-family: var(--font-display); font-size: 1.25rem; font-weight: 800;
               letter-spacing: 0.5px; text-transform: uppercase; line-height: 1.1; }}
.brand-sub {{ font-size: 0.7rem; color: var(--muted); font-weight: 400;
              letter-spacing: 2px; text-transform: uppercase; margin-top: 1px; }}

/* COUNTDOWN */
.countdown-wrap {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
.countdown-label {{ font-family: var(--font-display); font-size: 0.65rem; font-weight: 700;
    letter-spacing: 2px; color: var(--muted); text-transform: uppercase; white-space: nowrap; }}
.countdown-race {{ font-family: var(--font-display); font-size: 0.85rem; font-weight: 800;
    color: var(--red); text-transform: uppercase; letter-spacing: 1px; white-space: nowrap; }}
.countdown-timer {{ display: flex; gap: 6px; }}
.countdown-unit {{ text-align: center; }}
.countdown-num {{ font-family: var(--font-display); font-size: 1.5rem; font-weight: 800;
    color: var(--text); line-height: 1; display: block; min-width: 34px; }}
.countdown-unit-label {{ font-size: 0.58rem; color: var(--muted); letter-spacing: 1px;
    text-transform: uppercase; display: block; }}
.countdown-sep {{ font-family: var(--font-display); font-size: 1.3rem; font-weight: 700;
    color: var(--red); align-self: flex-start; margin-top: 2px; }}

/* NAV */
.tab-nav {{ background: var(--bg-2); border-bottom: 1px solid var(--border);
    overflow-x: auto; scrollbar-width: none; }}
.tab-nav::-webkit-scrollbar {{ display: none; }}
.tab-nav-inner {{ max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; }}
.tab-btn {{ font-family: var(--font-display); font-size: 0.85rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; color: var(--muted);
    background: none; border: none; border-bottom: 3px solid transparent;
    padding: 14px 18px; cursor: pointer; white-space: nowrap;
    transition: color 0.2s, border-color 0.2s; }}
.tab-btn:hover {{ color: var(--text); }}
.tab-btn.active {{ color: var(--text); border-bottom-color: var(--red); }}

/* MAIN */
.main {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 80px; }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; animation: fadeIn 0.25s ease; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; }} }}

.section-heading {{ font-family: var(--font-display); font-size: 2rem; font-weight: 800;
    letter-spacing: -0.5px; text-transform: uppercase; margin-bottom: 8px; line-height: 1; }}
.section-heading span {{ color: var(--red); }}
.section-label {{ font-family: var(--font-display); font-size: 0.72rem; font-weight: 700;
    letter-spacing: 2.5px; text-transform: uppercase; color: var(--muted);
    margin-bottom: 12px; margin-top: 4px; }}

/* TABLA */
.table-wrapper {{ overflow-x: auto; border-radius: 12px; border: 1px solid var(--border);
    background: var(--bg-2); -webkit-overflow-scrolling: touch; }}
.data-table {{ width: 100%; border-collapse: collapse; min-width: 480px; }}
.data-table th {{ font-family: var(--font-display); font-size: 0.72rem; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase; color: var(--muted);
    padding: 14px 16px; border-bottom: 1px solid var(--border);
    text-align: left; background: var(--bg-3); white-space: nowrap; }}
.data-table td {{ padding: 13px 16px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
.data-table tr:last-child td {{ border-bottom: none; }}
.data-table tr:hover td {{ background: rgba(255,255,255,0.025); }}
.data-table .row-first td {{ background: rgba(225,6,0,0.05); }}
.leaderboard {{ min-width: 520px; }}

.medal {{ display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%;
    font-family: var(--font-display); font-weight: 800; font-size: 0.85rem; }}
.medal.gold   {{ background: rgba(255,215,0,0.15);   color: var(--gold);   border: 1px solid rgba(255,215,0,0.3); }}
.medal.silver {{ background: rgba(192,192,192,0.12); color: var(--silver); border: 1px solid rgba(192,192,192,0.25); }}
.medal.bronze {{ background: rgba(205,127,50,0.12);  color: var(--bronze); border: 1px solid rgba(205,127,50,0.25); }}
.medal.plain  {{ background: var(--bg-4); color: var(--muted); border: 1px solid var(--border); }}

.driver-name  {{ display: block; font-weight: 600; font-size: 0.92rem; }}
.driver-email {{ display: block; font-size: 0.76rem; color: var(--muted); margin-top: 1px; }}
.pts-big  {{ font-family: var(--font-display); font-size: 1.35rem; font-weight: 800; }}
.pts-chip {{ font-family: var(--font-display); font-size: 1rem; font-weight: 700;
    background: var(--bg-4); padding: 3px 10px; border-radius: 6px; border: 1px solid var(--border); }}
.pts-tag {{ font-size: 0.7rem; color: var(--muted); font-weight: 400; }}
.trend-up      {{ color: var(--green);   font-weight: 700; font-size: 0.85rem; }}
.trend-down    {{ color: var(--danger);  font-weight: 700; font-size: 0.85rem; }}
.trend-neutral {{ color: var(--muted-2); font-weight: 700; }}

.divider {{ height: 1px; background: var(--border); margin: 28px 0; }}

/* CHARTS */
.chart-block {{ background: var(--bg-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; margin-bottom: 20px; }}
.chart-title {{ font-family: var(--font-display); font-size: 0.72rem; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 16px; }}
.chart-img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}

/* EXPORTAR */
.export-bar {{ display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }}
.export-btn {{ font-family: var(--font-display); font-size: 0.78rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; background: var(--bg-3);
    border: 1px solid var(--border-bright); color: var(--text);
    padding: 9px 18px; border-radius: 8px; cursor: pointer;
    transition: background 0.15s, border-color 0.15s; }}
.export-btn:hover {{ background: var(--bg-4); border-color: var(--red); color: var(--red); }}
.export-btn.primary {{ background: var(--red); border-color: var(--red); color: #fff; }}
.export-btn.primary:hover {{ background: #c50500; }}

/* RACE ACCORDION */
.race-block {{ border: 1px solid var(--border); border-radius: 12px; overflow: hidden;
    margin-bottom: 10px; background: var(--bg-2); }}
.race-header {{ width: 100%; background: var(--bg-3); border: none; color: var(--text);
    padding: 16px 20px; display: flex; align-items: center; justify-content: space-between;
    cursor: pointer; transition: background 0.15s; gap: 12px; }}
.race-header:hover {{ background: var(--bg-4); }}
.race-title-wrap {{ display: flex; align-items: center; gap: 12px; }}
.race-badge {{ font-family: var(--font-display); font-size: 0.72rem; font-weight: 800;
    letter-spacing: 1.5px; background: var(--red); color: #fff;
    padding: 3px 8px; border-radius: 5px; flex-shrink: 0; }}
.race-title {{ font-family: var(--font-display); font-size: 1.05rem; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase; }}
.toggle-icon {{ font-size: 1.3rem; color: var(--muted); font-style: normal;
    transition: transform 0.2s; flex-shrink: 0; line-height: 1; }}
.race-body {{ display: none; padding: 20px; border-top: 1px solid var(--border); }}

/* DETAIL ACCORDION */
.detail-row {{ border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin-bottom: 8px; }}
.detail-toggle {{ width: 100%; background: var(--bg-4); border: none; color: var(--text);
    padding: 12px 16px; display: flex; align-items: center; justify-content: space-between;
    cursor: pointer; font-size: 0.88rem; font-weight: 600; transition: background 0.15s; gap: 8px; }}
.detail-toggle:hover {{ background: #262626; }}
.detail-body {{ display: none; padding: 14px 16px; background: var(--bg-2);
    border-top: 1px solid var(--border); }}
.detail-text {{ font-size: 0.85rem; color: #CCCCCC; line-height: 1.7; }}

/* STATS */
.stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px; margin-bottom: 24px; }}
.stat-card {{ background: var(--bg-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px 16px; text-align: center; }}
.stat-card.accent {{ border-color: var(--red); background: rgba(225,6,0,0.06); }}
.stat-num  {{ font-family: var(--font-display); font-size: 2.4rem; font-weight: 800;
    color: var(--text); line-height: 1; margin-bottom: 6px; }}
.stat-desc {{ font-size: 0.76rem; color: var(--muted); text-transform: uppercase;
    letter-spacing: 1px; font-family: var(--font-display); }}
.leader-banner {{ background: rgba(225,6,0,0.08); border: 1px solid rgba(225,6,0,0.25);
    border-radius: 12px; padding: 20px 24px; margin-bottom: 28px;
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
.leader-label {{ font-family: var(--font-display); font-size: 0.68rem; letter-spacing: 3px;
    font-weight: 800; color: var(--red); text-transform: uppercase; flex-shrink: 0; }}
.leader-name  {{ font-family: var(--font-display); font-size: 1.4rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.5px; }}
.leader-email {{ font-size: 0.8rem; color: var(--muted); margin-left: auto; }}

/* CALENDARIO */
.cal-table {{ min-width: 560px; }}
.cal-jornada {{ font-family: var(--font-display); font-weight: 700; font-size: 0.85rem; color: var(--red); }}
.cal-carrera {{ font-family: var(--font-display); font-weight: 700; font-size: 0.95rem; letter-spacing: 0.5px; }}
.cal-cancelled td {{ opacity: 0.35; }}

/* RADAR */
.radar-block {{ background: var(--bg-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 20px; margin-bottom: 16px; text-align: center; }}
.radar-label {{ font-family: var(--font-display); font-size: 0.72rem; font-weight: 700;
    letter-spacing: 2.5px; text-transform: uppercase; color: var(--red); margin-bottom: 16px; }}

/* PERFILES */
.perfiles-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
    gap: 16px; }}
.perfil-card {{ background: var(--bg-2); border: 1px solid var(--border);
    border-radius: 14px; overflow: hidden; }}
.perfil-header {{ display: flex; align-items: center; gap: 14px; padding: 18px 20px;
    background: var(--bg-3); border-bottom: 1px solid var(--border); }}
.perfil-avatar {{ width: 48px; height: 48px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-family: var(--font-display);
    font-weight: 800; font-size: 1.1rem; flex-shrink: 0; }}
.perfil-info {{ flex: 1; min-width: 0; }}
.perfil-nombre {{ font-family: var(--font-display); font-size: 1.1rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.5px; white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; }}
.perfil-email {{ font-size: 0.75rem; color: var(--muted); white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis; }}
.perfil-pos-wrap {{ display: flex; flex-direction: column; align-items: center;
    gap: 4px; flex-shrink: 0; }}
.perfil-pts {{ font-family: var(--font-display); font-size: 1.6rem; font-weight: 800; line-height: 1; }}
.perfil-stats-mini {{ display: grid; grid-template-columns: repeat(4, 1fr);
    border-bottom: 1px solid var(--border); }}
.perfil-stat {{ padding: 14px 10px; text-align: center;
    border-right: 1px solid var(--border); }}
.perfil-stat:last-child {{ border-right: none; }}
.perfil-stat-num   {{ font-family: var(--font-display); font-size: 1.4rem; font-weight: 800;
    color: var(--text); line-height: 1; }}
.perfil-stat-label {{ font-size: 0.65rem; color: var(--muted); text-transform: uppercase;
    letter-spacing: 0.8px; margin-top: 3px; line-height: 1.3; }}
.perfil-spark-wrap {{ padding: 16px 16px 8px; border-bottom: 1px solid var(--border); }}
.spark-img {{ width: 100%; height: auto; display: block; border-radius: 6px; }}
.perfil-hist-toggle {{ padding: 4px 0; }}

/* EMPTY */
.empty-msg {{ color: var(--muted); font-size: 0.9rem; font-style: italic; padding: 24px 0; }}

/* FOOTER */
.site-footer {{ border-top: 1px solid var(--border); padding: 20px;
    text-align: center; font-size: 0.78rem; color: var(--muted-2); }}
.footer-stripe {{ width: 32px; height: 3px; background: var(--red);
    border-radius: 2px; margin: 0 auto 12px; }}

/* PRINT */
@media print {{
    .site-header, .tab-nav, .export-bar, .detail-toggle, .race-header {{ display: none !important; }}
    .tab-panel {{ display: block !important; page-break-after: always; }}
    body {{ background: #fff; color: #000; }}
}}

/* RESPONSIVE */
@media (max-width: 640px) {{
    .header-inner {{ min-height: 56px; padding: 8px 14px; }}
    .brand-text {{ font-size: 1rem; }}
    .countdown-num {{ font-size: 1.2rem; min-width: 26px; }}
    .main {{ padding: 20px 14px 60px; }}
    .section-heading {{ font-size: 1.5rem; }}
    .tab-btn {{ padding: 12px 12px; font-size: 0.78rem; letter-spacing: 1px; }}
    .stats-grid {{ grid-template-columns: 1fr 1fr; }}
    .leader-email {{ display: none; }}
    .race-body, .race-header {{ padding: 14px; }}
    .data-table th, .data-table td {{ padding: 11px 12px; }}
    .stat-num {{ font-size: 2rem; }}
    .perfiles-grid {{ grid-template-columns: 1fr; }}
    .perfil-stats-mini {{ grid-template-columns: repeat(2, 1fr); }}
    .perfil-stat:nth-child(2) {{ border-right: none; }}
    .perfil-stat:nth-child(3) {{ border-top: 1px solid var(--border); }}
    .countdown-wrap {{ gap: 6px; }}
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
    <div class="countdown-wrap">
        <div>
            <div class="countdown-label">Próxima carrera</div>
            <div class="countdown-race" id="cd-race">{proxima_carrera}</div>
        </div>
        <div class="countdown-timer" id="cd-timer">
            <div class="countdown-unit">
                <span class="countdown-num" id="cd-d">--</span>
                <span class="countdown-unit-label">días</span>
            </div>
            <span class="countdown-sep">:</span>
            <div class="countdown-unit">
                <span class="countdown-num" id="cd-h">--</span>
                <span class="countdown-unit-label">horas</span>
            </div>
            <span class="countdown-sep">:</span>
            <div class="countdown-unit">
                <span class="countdown-num" id="cd-m">--</span>
                <span class="countdown-unit-label">min</span>
            </div>
            <span class="countdown-sep">:</span>
            <div class="countdown-unit">
                <span class="countdown-num" id="cd-s">--</span>
                <span class="countdown-unit-label">seg</span>
            </div>
        </div>
    </div>
</div>
</header>

<nav class="tab-nav">
<div class="tab-nav-inner">
    <button class="tab-btn active" onclick="openTab(event,'panel-acumulado')">Acumulado</button>
    <button class="tab-btn" onclick="openTab(event,'panel-carreras')">Por Carrera</button>
    <button class="tab-btn" onclick="openTab(event,'panel-graficos')">Gráficos</button>
    <button class="tab-btn" onclick="openTab(event,'panel-perfiles')">Perfiles</button>
    <button class="tab-btn" onclick="openTab(event,'panel-stats')">Estadísticas</button>
    <button class="tab-btn" onclick="openTab(event,'panel-calendario')">Calendario</button>
</div>
</nav>

<main class="main" id="main-content">

<div id="panel-acumulado" class="tab-panel active">
    <h2 class="section-heading">Ranking <span>General</span></h2>
    <p class="section-label" style="margin-bottom:16px;">Puntos acumulados · Todas las carreras</p>
    <div class="export-bar">
        <button class="export-btn primary" onclick="exportarImagen()">⬇ Exportar imagen</button>
        <button class="export-btn" onclick="exportarCSV()">⬇ Exportar CSV</button>
        <button class="export-btn" onclick="window.print()">🖨 Imprimir / PDF</button>
    </div>
    <div id="ranking-export-target">
        {ranking_acumulado_html}
    </div>
    <div class="divider"></div>
    <div class="chart-block">
        <div class="chart-title">Distribución de puntos</div>
        {graf_barras_html}
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
        {graf_evol_html}
    </div>
    <div class="chart-block">
        <div class="chart-title">Historial de posiciones carrera a carrera (bump chart)</div>
        {bump_html}
    </div>
    <div class="section-label" style="margin-top:32px;">Perfil de aciertos por carrera · Radar Top 8</div>
    {radars_html}
</div>

<div id="panel-perfiles" class="tab-panel">
    <h2 class="section-heading">Per<span>files</span></h2>
    <p class="section-label" style="margin-bottom:20px;">Estadísticas individuales de cada participante</p>
    <div class="perfiles-grid">
        {perfiles_html}
    </div>
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
// ===== TABS =====
function openTab(evt, panelId) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(panelId).classList.add('active');
    evt.currentTarget.classList.add('active');
}}

// ===== ACCORDION =====
function toggleDetail(id) {{
    const el   = document.getElementById(id);
    const icon = document.getElementById('icon-' + id);
    const open = el.style.display === 'block';
    el.style.display  = open ? 'none' : 'block';
    if (icon) icon.textContent = open ? '＋' : '－';
}}

// ===== IR A PERFIL =====
function irPerfil(idx) {{
    const btn = document.querySelector('.tab-btn[onclick*="panel-perfiles"]');
    if (btn) btn.click();
    setTimeout(() => {{
        const card = document.getElementById('perfil-' + idx);
        if (card) card.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}, 120);
}}

// ===== COUNTDOWN =====
(function() {{
    const iso = "{proxima_iso}";
    if (!iso) {{ document.getElementById('cd-timer').style.display = 'none'; return; }}
    const target = new Date(iso);
    function tick() {{
        const diff = target - new Date();
        if (diff <= 0) {{
            ['cd-d','cd-h','cd-m','cd-s'].forEach(id => document.getElementById(id).textContent = '00');
            return;
        }}
        const d = Math.floor(diff / 86400000);
        const h = Math.floor((diff % 86400000) / 3600000);
        const m = Math.floor((diff % 3600000)  / 60000);
        const s = Math.floor((diff % 60000)    / 1000);
        document.getElementById('cd-d').textContent = String(d).padStart(2,'0');
        document.getElementById('cd-h').textContent = String(h).padStart(2,'0');
        document.getElementById('cd-m').textContent = String(m).padStart(2,'0');
        document.getElementById('cd-s').textContent = String(s).padStart(2,'0');
    }}
    tick();
    setInterval(tick, 1000);
}})();

// ===== EXPORTAR IMAGEN (html2canvas via CDN) =====
function exportarImagen() {{
    const script = document.createElement('script');
    script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    script.onload = function() {{
        const target = document.getElementById('ranking-export-target');
        html2canvas(target, {{
            backgroundColor: '#111111',
            scale: 2,
            useCORS: true,
            logging: false
        }}).then(canvas => {{
            const link = document.createElement('a');
            link.download = 'ranking_f1_2026.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
        }});
    }};
    document.head.appendChild(script);
}}

// ===== EXPORTAR CSV =====
function exportarCSV() {{
    const rows = document.querySelectorAll('#ranking-export-target table tr');
    if (!rows.length) return;
    let csv = '';
    rows.forEach(tr => {{
        const cols = Array.from(tr.querySelectorAll('th, td')).map(td => {{
            return '"' + (td.innerText || td.textContent).replace(/"/g, '""').trim() + '"';
        }});
        csv += cols.join(',') + '\\n';
    }});
    const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
    const url  = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url; link.download = 'ranking_f1_2026.csv'; link.click();
    URL.revokeObjectURL(url);
}}
</script>
</body>
</html>"""

# =========================
# MAIN
# =========================
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

    # Orden según el calendario (ignorando tachados)
    orden_calendario = [
        re.sub(r'<[^>]+>', '', entry["Carrera"]).strip().capitalize()
        for entry in CALENDARIO
    ]

    # Mapear nombre de carrera → nombre de archivo
    csv_por_carrera = {}
    for archivo in os.listdir(CARPETA_RESPUESTAS):
        if archivo.endswith(".csv"):
            nombre = archivo.replace("respuestas_", "").replace(".csv", "").capitalize()
            csv_por_carrera[nombre] = archivo

    # Ordenar según calendario, con los no-encontrados al final
    archivos_ordenados = []
    for nombre in orden_calendario:
        if nombre in csv_por_carrera:
            archivos_ordenados.append(csv_por_carrera[nombre])
    for nombre, archivo in csv_por_carrera.items():
        if archivo not in archivos_ordenados:
            archivos_ordenados.append(archivo)

    for archivo in archivos_ordenados:
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
    bump_chart = generar_bump_chart(all_rankings)
    radars_data = generar_radar_por_carrera(all_dfs, top_n=8)
    stats_adicionales = generar_estadisticas_adicionales(all_dfs, ranking_acumulado)
    perfiles_html = generar_perfiles_html(all_rankings, all_dfs, ranking_acumulado)

    html_content = generar_html(
        rankings_por_carrera, ranking_acumulado,
        grafico_barras, grafico_evolucion, bump_chart,
        radars_data, stats_adicionales, perfiles_html
    )

    with open("ranking_f1.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("🏁 HTML generado: ranking_f1.html")
    print("   Abrilo en cualquier navegador o celular.")

if __name__ == "__main__":
    main()