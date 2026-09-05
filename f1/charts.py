# -*- coding: utf-8 -*-
"""Graficos de matplotlib embebidos como PNG en base64."""

import base64
from io import BytesIO

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

from .calendario import carreras_en_orden

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
    ax.set_facecolor('#0D0D0D'); fig.patch.set_facecolor('#0D0D0D')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333333'); ax.spines['left'].set_visible(False)
    ax.set_axisbelow(True); ax.xaxis.grid(True, color='#1E1E1E', linewidth=0.8)
    plt.tight_layout(pad=1.5)
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches='tight', dpi=130); buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')
def generar_sparkline_perfil(email: str, all_rankings: pd.DataFrame) -> str:
    data = all_rankings[all_rankings["Dirección de correo electrónico"] == email]
    if data.empty:
        return ""
    carreras = carreras_en_orden(data['Carrera'].unique().tolist())
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
    ax.set_facecolor('#0D0D0D'); fig.patch.set_facecolor('#0D0D0D')
    for spine in ax.spines.values(): spine.set_visible(False)
    plt.tight_layout(pad=0.3)
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches='tight', dpi=120); buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')
