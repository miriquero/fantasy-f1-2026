import pandas as pd
import os
import json
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime

# =========================
# CONFIGURACIÓN GENERAL
# =========================
# Carpeta donde se guardan los CSV de respuestas (uno por carrera)
CARPETA_RESPUESTAS = "respuestas"  # Crea esta carpeta y agrega los CSV allí

# Archivo JSON con resultados reales por carrera (crea este archivo manualmente)
ARCHIVO_RESULTADOS = "resultados.json"

# Lista oficial de pilotos (agrega si faltan)
PILOTOS = [
    "Max Verstappen", "Arvid Lindblad", "Charles Leclerc", "Lewis Hamilton",
    "Oscar Piastri", "Lando Norris", "George Russell", "Kimi Antonelli",
    "Pierre Gasly", "Franco Colapinto", "Carlos Sainz", "Alex Albon",
    "Esteban Ocon", "Ollie Bearman", "Liam Lawson", "Isack Hadjar",
    "Fernando Alonso", "Lance Stroll", "Gabriel Bortoletto", "Nico Hulkenberg",
    "Valtteri Bottas", "Sergio Perez", "Yuki Tsunoda"
]

# Nombres de columnas de puestos
COL_PUESTOS = [
    "Primer puesto", "Segundo puesto", "Tercer puesto", "Cuarto puesto",
    "Quinto puesto", "Sexto puesto", "Séptimo puesto", "Octavo puesto",
    "Noveno puesto", "Décimo puesto"
]

# Calendario de carreras 2026 (basado en la imagen proporcionada)
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
def procesar_carrera(nombre_carrera: str, archivo_csv: str, resultados: Dict) -> pd.DataFrame:
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
            cambios[email] = f'<span style="color:#22c55e">↑{diff}</span>'
        elif diff < 0:
            cambios[email] = f'<span style="color:#ef4444">↓{-diff}</span>'
        else:
            cambios[email] = '—'
    
    ranking_acumulado['Cambio'] = ranking_acumulado['Dirección de correo electrónico'].map(cambios)
    return ranking_acumulado

# =========================
# GENERAR GRÁFICOS (MEJORADOS VISUALMENTE)
# =========================
def generar_grafico_barras_acumulado(ranking_acumulado: pd.DataFrame) -> str:
    if ranking_acumulado.empty:
        return ""
    
    fig, ax = plt.subplots(figsize=(10, len(ranking_acumulado) * 0.35 + 1))
    ax.barh(ranking_acumulado["Dirección de correo electrónico"], ranking_acumulado["Puntos"], color='#E10600')
    ax.set_title('Puntos Acumulados', color='#FFFFFF', fontsize=14, pad=15)
    ax.set_xlabel('Puntos', color='#FFFFFF')
    ax.invert_yaxis()
    ax.tick_params(colors='#FFFFFF')
    ax.set_facecolor('#111111')
    fig.patch.set_facecolor('#111111')
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generar_grafico_evolucion(all_rankings: pd.DataFrame, top_n=5) -> str:
    if all_rankings.empty:
        return ""
    
    pivot = all_rankings.pivot_table(index="Dirección de correo electrónico", columns="Carrera", values="Puntos", fill_value=0).cumsum(axis=1)
    top_emails = pivot.iloc[:, -1].nlargest(top_n).index
    carreras_ordenadas = sorted(pivot.columns)
    pivot = pivot[carreras_ordenadas]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ['#E10600', '#00D4FF', '#FFD700', '#FF00FF', '#00FF9F']
    for i, email in enumerate(top_emails):
        ax.plot(pivot.columns, pivot.loc[email], marker='o', linewidth=2.5, markersize=6, label=email.split('@')[0], color=colors[i % len(colors)])
    ax.set_title('Evolución de Puntos - Top 5', color='#FFFFFF', fontsize=14)
    ax.set_xlabel('Carreras', color='#FFFFFF')
    ax.set_ylabel('Puntos Acumulados', color='#FFFFFF')
    ax.legend(loc='upper left', labelcolor='#FFFFFF', frameon=False)
    ax.grid(True, color='#333333', linestyle='--')
    ax.tick_params(colors='#FFFFFF')
    ax.set_facecolor('#111111')
    fig.patch.set_facecolor('#111111')
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

def generar_grafico_pastel_participacion(all_dfs: List[pd.DataFrame]) -> str:
    if not all_dfs:
        return ""
    
    participacion = pd.concat(all_dfs)['Carrera'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(participacion, labels=participacion.index, autopct='%1.1f%%', colors=['#E10600', '#00D4FF', '#FFD700', '#FF00FF'])
    ax.set_title('Participación por Carrera', color='#FFFFFF', fontsize=14)
    fig.patch.set_facecolor('#111111')
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')

# =========================
# GENERAR ESTADÍSTICAS ADICIONALES
# =========================
def generar_estadisticas_adicionales(all_dfs: List[pd.DataFrame], ranking_acumulado: pd.DataFrame) -> str:
    if not all_dfs:
        return "<p>No hay datos disponibles.</p>"
    
    df_all = pd.concat(all_dfs)
    total_participantes = df_all['Dirección de correo electrónico'].nunique()
    total_predicciones = len(df_all)
    puntos_totales = df_all['Puntos'].sum()
    promedio_puntos = puntos_totales / total_predicciones if total_predicciones > 0 else 0
    lider = ranking_acumulado.iloc[0]['Dirección de correo electrónico'] if not ranking_acumulado.empty else "N/A"
    
    maximos_por_carrera = df_all.groupby('Carrera')['Puntos'].max()
    maximos_html = "".join([f"<li>{carrera}: {puntos} puntos</li>" for carrera, puntos in maximos_por_carrera.items()])
    
    return f"""
    <div class="stats-container">
        <h3>Estadísticas Generales</h3>
        <ul>
            <li>Participantes únicos: {total_participantes}</li>
            <li>Predicciones totales: {total_predicciones}</li>
            <li>Puntos totales distribuidos: {puntos_totales}</li>
            <li>Promedio por predicción: {promedio_puntos:.2f}</li>
            <li>Líder actual: {lider}</li>
        </ul>
        <h4>Máximos por Carrera</h4>
        <ul>{maximos_html}</ul>
    </div>
    """

# =========================
# GENERAR HTML PROFESIONAL (VERSIÓN MEJORADA PARA MÓVIL)
# =========================
def generar_html(rankings_por_carrera: List[pd.DataFrame], ranking_acumulado: pd.DataFrame,
                 grafico_barras: str, grafico_evolucion: str, grafico_pastel: str,
                 stats_adicionales: str) -> str:
    
    calendario_df = pd.DataFrame(CALENDARIO)
    
    # HTML base (con CSS ultra-optimizado para móviles)
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ranking F1 Predicciones - Temporada 2026</title>
        <!-- FAVICON OFICIAL F1 -->
        <link rel="icon" href="https://www.formula1.com/etc/designs/f1/img/favicon.ico" type="image/x-icon">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
            
            :root {{
                --primary-red: #E10600;
                --dark-bg: #0F0F0F;
                --card-bg: #1A1A1A;
                --text: #FFFFFF;
            }}
            
            body {{
                font-family: 'Inter', system-ui, sans-serif;
                background-color: var(--dark-bg);
                color: var(--text);
                margin: 0;
                padding: 0;
                line-height: 1.6;
            }}
            
            header {{
                background: linear-gradient(90deg, #111111, #1F1F1F);
                padding: 20px 0;
                text-align: center;
                position: relative;
                border-bottom: 4px solid var(--primary-red);
            }}
            
            header h1 {{
                margin: 0;
                font-size: 2rem;
                font-weight: 700;
                letter-spacing: -0.5px;
            }}
            
            nav {{
                background-color: #111111;
                padding: 12px 0;
                border-bottom: 1px solid #333;
            }}
            
            nav ul {{
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                justify-content: center;
                gap: 20px;
                flex-wrap: wrap;
            }}
            
            nav a {{
                color: #CCCCCC;
                text-decoration: none;
                font-weight: 500;
                transition: color 0.2s;
            }}
            
            nav a:hover {{
                color: var(--primary-red);
            }}
            
            .tab-container {{
                max-width: 1280px;
                margin: 30px auto;
                padding: 0 15px;
            }}
            
            .tab-buttons {{
                display: flex;
                background: #111111;
                border-radius: 12px;
                padding: 6px;
                margin-bottom: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.4);
            }}
            
            .tab-button {{
                flex: 1;
                background: transparent;
                border: none;
                color: #AAAAAA;
                padding: 14px 20px;
                font-size: 1rem;
                font-weight: 600;
                border-radius: 10px;
                transition: all 0.3s;
            }}
            
            .tab-button.active {{
                background: var(--primary-red);
                color: white;
                box-shadow: 0 4px 10px rgba(225,6,0,0.3);
            }}
            
            .tab-content {{
                display: none;
                background: var(--card-bg);
                border-radius: 16px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }}
            
            .tab-content.active {{
                display: block;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                background: #111111;
                border-radius: 12px;
                overflow: hidden;
            }}
            
            th {{
                background: var(--primary-red);
                color: white;
                padding: 16px 12px;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 0.5px;
            }}
            
            td {{
                padding: 16px 12px;
                border-bottom: 1px solid #222;
            }}
            
            tr:last-child td {{
                border-bottom: none;
            }}
            
            tr:hover {{
                background: #1F1F1F;
            }}
            
            .table-wrapper {{
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                margin: 20px 0;
                border-radius: 12px;
                background: #111111;
            }}
            
            .table-wrapper table {{
                min-width: 700px;
                width: 100%;
            }}
            
            .chart-container {{
                text-align: center;
                margin: 25px 0;
                background: #111111;
                padding: 20px;
                border-radius: 16px;
            }}
            
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            
            .stats-container {{
                background: #111111;
                padding: 25px;
                border-radius: 16px;
            }}
            
            .accordion {{
                margin-bottom: 12px;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            }}
            
            .accordion-button {{
                background: #1F1F1F;
                color: white;
                padding: 16px 20px;
                width: 100%;
                text-align: left;
                border: none;
                font-weight: 500;
                transition: background 0.2s;
            }}
            
            .accordion-button:hover {{
                background: #2A2A2A;
            }}
            
            .accordion-content {{
                background: #111111;
                padding: 20px;
                display: none;
            }}
            
            footer {{
                text-align: center;
                padding: 20px;
                background: #0A0A0A;
                color: #666;
                font-size: 0.9rem;
            }}
            
            /* ==================== RESPONSIVE MÓVIL ==================== */
            @media (max-width: 768px) {{
                header h1 {{
                    font-size: 1.65rem;
                }}
                
                nav ul {{
                    gap: 12px;
                    justify-content: center;
                }}
                
                nav a {{
                    font-size: 0.9rem;
                }}
                
                .tab-buttons {{
                    flex-direction: column;
                }}
                
                .tab-button {{
                    padding: 14px 16px;
                    font-size: 0.95rem;
                }}
                
                .tab-content {{
                    padding: 18px 12px;
                }}
                
                .stats-container {{
                    padding: 18px;
                }}
                
                th, td {{
                    padding: 12px 8px;
                    font-size: 0.82rem;
                }}
                
                .table-wrapper {{
                    margin: 15px 0;
                }}
                
                .chart-container {{
                    padding: 12px;
                }}
                
                .accordion-button {{
                    padding: 14px 16px;
                    font-size: 0.95rem;
                }}
                
                .accordion-content {{
                    padding: 15px;
                }}
            }}
            
            .calendar-table th {{
                background: #1F1F1F;
            }}
        </style>
        <script>
            function openTab(evt, tabName) {{
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
                document.getElementById(tabName).classList.add('active');
                evt.currentTarget.classList.add('active');
            }}
            
            function toggleAccordion(id) {{
                const content = document.getElementById(id);
                content.style.display = content.style.display === 'block' ? 'none' : 'block';
            }}
        </script>
    </head>
    <body>
        <header>
            <h1>🏁 Ranking de Predicciones F1 - Temporada 2026</h1>
        </header>
        
        <nav>
            <ul>
                <li><a href="#acumulado" onclick="document.querySelector('.tab-button[onclick*=\\'acumulado\\']').click();">Acumulado</a></li>
                <li><a href="#por-carrera" onclick="document.querySelector('.tab-button[onclick*=\\'por-carrera\\']').click();">Por Carrera</a></li>
                <li><a href="#graficos" onclick="document.querySelector('.tab-button[onclick*=\\'graficos\\']').click();">Gráficos</a></li>
                <li><a href="#estadisticas" onclick="document.querySelector('.tab-button[onclick*=\\'estadisticas\\']').click();">Estadísticas</a></li>
                <li><a href="#calendario" onclick="document.querySelector('.tab-button[onclick*=\\'calendario\\']').click();">Calendario</a></li>
            </ul>
        </nav>
        
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="openTab(event, 'acumulado')">Ranking Acumulado</button>
                <button class="tab-button" onclick="openTab(event, 'por-carrera')">Rankings por Carrera</button>
                <button class="tab-button" onclick="openTab(event, 'graficos')">Gráficos</button>
                <button class="tab-button" onclick="openTab(event, 'estadisticas')">Estadísticas</button>
                <button class="tab-button" onclick="openTab(event, 'calendario')">Calendario</button>
            </div>
            
            <div id="acumulado" class="tab-content active">
                <h2>Ranking Acumulado General</h2>
                {ranking_acumulado_html}
                <div class="chart-container">
                    <h3>Gráfico de Puntos Acumulados</h3>
                    <img src="data:image/png;base64,{grafico_barras}" alt="Gráfico Acumulado">
                </div>
            </div>
            
            <div id="por-carrera" class="tab-content">
                <h2>Rankings por Carrera</h2>
                {rankings_por_carrera_html}
            </div>
            
            <div id="graficos" class="tab-content">
                <h2>Gráficos y Visualizaciones</h2>
                <div class="chart-container">
                    <h3>Evolución de Puntos (Top 5)</h3>
                    <img src="data:image/png;base64,{grafico_evolucion}" alt="Evolución">
                </div>
                <div class="chart-container">
                    <h3>Participación por Carrera</h3>
                    <img src="data:image/png;base64,{grafico_pastel}" alt="Pastel">
                </div>
            </div>
            
            <div id="estadisticas" class="tab-content">
                <h2>Estadísticas Adicionales</h2>
                {stats_adicionales}
            </div>
            
            <div id="calendario" class="tab-content">
                <h2>Calendario Oficial F1 2026</h2>
                <p style="color:#AAAAAA; margin-bottom:20px;">Horarios completos con hora local y ajustada a Argentina (GMT-3)</p>
                {calendario_html}
            </div>
        </div>
        
        <footer>
            <p>Generado automáticamente — {fecha_actual}</p>
        </footer>
    </body>
    </html>
    """
    
    # ==================== INSERCIÓN DE CONTENIDO (CON WRAPPERS PARA MÓVIL) ====================
    if not ranking_acumulado.empty:
        ranking_acumulado_html = f'<div class="table-wrapper">{ranking_acumulado.to_html(index=False, classes="ranking-table", escape=False)}</div>'
    else:
        ranking_acumulado_html = "<p>No hay datos disponibles.</p>"
    
    rankings_por_carrera_html = ""
    for i, ranking in enumerate(rankings_por_carrera):
        carrera = ranking["Carrera"].iloc[0]
        ranking_table = f'<div class="table-wrapper">{ranking.drop(columns=["Carrera", "Detalles"]).to_html(index=False, classes="ranking-table")}</div>'
        
        detalles_html = ""
        for j, row in ranking.iterrows():
            email = row["Dirección de correo electrónico"]
            detalles = row["Detalles"]
            detalles_html += f"""
            <div class="accordion">
                <button class="accordion-button" onclick="toggleAccordion('det-{i}-{j}')">Detalles para {email}</button>
                <div id="det-{i}-{j}" class="accordion-content">
                    <p>{detalles}</p>
                </div>
            </div>
            """
        
        rankings_por_carrera_html += f"""
        <div class="accordion">
            <button class="accordion-button" onclick="toggleAccordion('acc-{i}')">{carrera}</button>
            <div id="acc-{i}" class="accordion-content">
                {ranking_table}
                <h3>Detalles por Participante</h3>
                {detalles_html}
            </div>
        </div>
        """
    
    calendario_html = f'<div class="table-wrapper">{calendario_df.to_html(index=False, classes="calendar-table", escape=False)}</div>'
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    return html.format(
        ranking_acumulado_html=ranking_acumulado_html,
        rankings_por_carrera_html=rankings_por_carrera_html,
        grafico_barras=grafico_barras,
        grafico_evolucion=grafico_evolucion,
        grafico_pastel=grafico_pastel,
        stats_adicionales=stats_adicionales,
        calendario_html=calendario_html,
        fecha_actual=fecha_actual
    )

# =========================
# MAIN: PROCESAR TODO
# =========================
def main():
    if not os.path.exists(CARPETA_RESPUESTAS):
        print(f"Carpeta '{CARPETA_RESPUESTAS}' no existe. Créala y agrega los CSV.")
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
    
    # Calcular acumulado
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
    
    # Generar gráficos
    grafico_barras = generar_grafico_barras_acumulado(ranking_acumulado)
    grafico_evolucion = generar_grafico_evolucion(all_rankings)
    grafico_pastel = generar_grafico_pastel_participacion(all_dfs)
    
    # Estadísticas
    stats_adicionales = generar_estadisticas_adicionales(all_dfs, ranking_acumulado)
    
    # Generar HTML (versión móvil optimizada)
    html_content = generar_html(rankings_por_carrera, ranking_acumulado, 
                                grafico_barras, grafico_evolucion, grafico_pastel, 
                                stats_adicionales)
    with open("ranking_f1.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("🏁 HTML generado: ranking_f1.html")
    print("Ábrelo en un navegador (o móvil) para ver el ranking PROFESIONAL y 100% responsive.")

if __name__ == "__main__":
    main()