import pandas as pd
import os
import json
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import base64
from io import BytesIO

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

# =========================
# FUNCIÓN PUNTOS POR POSICIÓN (ACTUALIZADA CON NUEVA REGLA)
# =========================
def puntos_posicion(predicha: int, real: int) -> int:
    if predicha == real:
        return 10
    elif abs(predicha - real) == 1:
        return 5
    else:
        return 1  # +1 si el piloto está en top 10 real, pero no exacto ni diff 1

# =========================
# CALCULAR PUNTOS Y DETALLES POR FILA (ACTUALIZADO PARA DESGLOSE)
# =========================
def calcular_puntos_y_detalles(row: pd.Series, posiciones_reales: Dict[str, int], vuelta_rapida_real: str, colapinto_real: int) -> Tuple[int, str]:
    puntos = 0
    detalles = []
    
    # Puntos por posiciones
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
    
    # Vuelta rápida
    vr = str(row.get("Vuelta Rápida", "")).strip()
    if vr == vuelta_rapida_real:
        puntos += 10
        detalles.append(f"Vuelta rápida: {vr} (+10)")
    
    # Posición de Colapinto
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
    
    # Corregir si colapinto_real es str: convertir a int
    if isinstance(colapinto_real, str):
        try:
            colapinto_real = convertir_posicion_a_numero(colapinto_real)
        except:
            colapinto_real = 0  # Si falla, default 0
    
    posiciones_reales = {piloto: i+1 for i, piloto in enumerate(resultado_carrera)}
    
    df[["Puntos", "Detalles"]] = df.apply(
        lambda row: pd.Series(calcular_puntos_y_detalles(row, posiciones_reales, vuelta_rapida_real, colapinto_real)),
        axis=1
    )
    df["Carrera"] = nombre_carrera
    
    # Ranking con detalles agregados
    ranking = df.groupby("Dirección de correo electrónico", as_index=False).agg({
        "Puntos": "sum",
        "Detalles": lambda x: "<br><br>".join(x)  # Concatenar detalles si múltiples envíos
    }).sort_values("Puntos", ascending=False).reset_index(drop=True)
    ranking["Posición"] = ranking.index + 1
    ranking = ranking[["Posición", "Dirección de correo electrónico", "Puntos", "Detalles"]]
    ranking["Carrera"] = nombre_carrera
    
    return ranking, df

# =========================
# CALCULAR CAMBIO DE POSICIONES (NUEVA FUNCIÓN PARA BADGE DE RACHA)
# =========================
def calcular_cambios_posiciones(all_rankings: pd.DataFrame, ranking_acumulado: pd.DataFrame) -> pd.DataFrame:
    if len(all_rankings['Carrera'].unique()) < 2:
        # Si solo una carrera, no hay previa
        ranking_acumulado['Cambio'] = '-'
        return ranking_acumulado
    
    # Ordenar carreras (asumiendo nombres como "Australia", pero para general, usa sorted)
    carreras = sorted(all_rankings['Carrera'].unique())
    
    # Acumulado actual (última carrera)
    acum_actual = all_rankings[all_rankings['Carrera'] == carreras[-1]].set_index('Dirección de correo electrónico')['Posición']
    
    # Acumulado previo (todas menos última)
    prev_rankings = all_rankings[all_rankings['Carrera'] != carreras[-1]]
    if prev_rankings.empty:
        acum_prev = pd.Series()  # Vacío si no hay previas
    else:
        acum_prev = prev_rankings.groupby("Dirección de correo electrónico")["Puntos"].sum().sort_values(ascending=False).reset_index()
        acum_prev["Posición"] = acum_prev.index + 1
        acum_prev = acum_prev.set_index('Dirección de correo electrónico')['Posición']
    
    # Calcular cambios
    cambios = {}
    for email in ranking_acumulado['Dirección de correo electrónico']:
        pos_actual = ranking_acumulado[ranking_acumulado['Dirección de correo electrónico'] == email]['Posición'].values[0]
        pos_prev = acum_prev.get(email, float('inf'))  # Si nuevo, inf (bajada desde fuera)
        diff = pos_prev - pos_actual
        if diff > 0:
            cambios[email] = f'<span style="color:green">↑{diff}</span>'
        elif diff < 0:
            cambios[email] = f'<span style="color:red">↓{-diff}</span>'
        else:
            cambios[email] = '-'
    
    # Agregar columna a acumulado final
    ranking_acumulado['Cambio'] = ranking_acumulado['Dirección de correo electrónico'].map(cambios)
    return ranking_acumulado

# =========================
# GENERAR GRÁFICOS
# =========================
def generar_grafico_barras_acumulado(ranking_acumulado: pd.DataFrame) -> str:
    if ranking_acumulado.empty:
        return ""
    
    fig, ax = plt.subplots(figsize=(10, len(ranking_acumulado) * 0.3 + 1))
    ax.barh(ranking_acumulado["Dirección de correo electrónico"], ranking_acumulado["Puntos"], color='#E10600')  # Rojo F1
    ax.set_title('Puntos Acumulados por Participante', color='white')
    ax.set_xlabel('Puntos', color='white')
    ax.set_ylabel('Participante', color='white')
    ax.invert_yaxis()
    ax.tick_params(colors='white')
    ax.set_facecolor('#1A1A1A')
    fig.patch.set_facecolor('#1A1A1A')
    
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

def generar_grafico_evolucion(all_rankings: pd.DataFrame, top_n=5) -> str:
    if all_rankings.empty:
        return ""
    
    pivot = all_rankings.pivot_table(
        index="Dirección de correo electrónico",
        columns="Carrera",
        values="Puntos",
        fill_value=0
    ).cumsum(axis=1)
    
    top_emails = pivot.iloc[:, -1].nlargest(top_n).index
    carreras_ordenadas = sorted(pivot.columns, key=lambda x: int(x.replace("Carrera", "")) if "Carrera" in x else 0)
    pivot = pivot[carreras_ordenadas]
    
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ['#E10600', '#FFFFFF', '#FFD700', '#00FFFF', '#FF69B4']  # Colores vibrantes F1
    for i, email in enumerate(top_emails):
        ax.plot(pivot.columns, pivot.loc[email], marker='o', label=email.split('@')[0], color=colors[i % len(colors)])
    
    ax.set_title(f'Evolución de Puntos - Top {top_n}', color='white')
    ax.set_xlabel('Carreras', color='white')
    ax.set_ylabel('Puntos Acumulados', color='white')
    ax.legend(loc='upper left', labelcolor='white')
    ax.grid(True, color='#333')
    ax.tick_params(colors='white')
    ax.set_facecolor('#1A1A1A')
    fig.patch.set_facecolor('#1A1A1A')
    
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

def generar_grafico_pastel_participacion(all_dfs: List[pd.DataFrame]) -> str:
    if not all_dfs:
        return ""
    
    all_data = pd.concat(all_dfs)
    participacion = all_data.groupby("Carrera")["Dirección de correo electrónico"].nunique()
    
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.pie(participacion, labels=participacion.index, autopct='%1.1f%%', colors=['#E10600', '#FFFFFF', '#1A1A1A', '#FFD700'])
    ax.set_title('Participación por Carrera', color='white')
    fig.patch.set_facecolor('#1A1A1A')
    
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', transparent=True)
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64

# =========================
# GENERAR ESTADÍSTICAS ADICIONALES
# =========================
def generar_estadisticas_adicionales(all_dfs: List[pd.DataFrame], ranking_acumulado: pd.DataFrame) -> str:
    if not all_dfs:
        return ""
    
    all_data = pd.concat(all_dfs)
    
    total_participantes = all_data["Dirección de correo electrónico"].nunique()
    promedio_puntos = all_data["Puntos"].mean()
    max_puntos_carrera = all_data.groupby("Carrera")["Puntos"].max().to_dict()
    mejor_predictor = ranking_acumulado.iloc[0]["Dirección de correo electrónico"] if not ranking_acumulado.empty else "N/A"
    total_predicciones = len(all_data)
    puntos_totales = all_data["Puntos"].sum()
    
    stats_html = """
    <div class="stats-container">
        <h3>Estadísticas Generales</h3>
        <ul>
            <li>Participantes únicos: {total_participantes}</li>
            <li>Predicciones totales: {total_predicciones}</li>
            <li>Puntos totales distribuidos: {puntos_totales}</li>
            <li>Promedio de puntos por predicción: {promedio_puntos:.2f}</li>
            <li>Líder actual: {mejor_predictor}</li>
        </ul>
        <h4>Máximos por Carrera</h4>
        <ul>
    """.format(total_participantes=total_participantes, total_predicciones=total_predicciones, 
               puntos_totales=puntos_totales, promedio_puntos=promedio_puntos, mejor_predictor=mejor_predictor)
    
    for carrera, max_pt in max_puntos_carrera.items():
        stats_html += f"<li>{carrera}: {max_pt} puntos</li>"
    
    stats_html += "</ul></div>"
    return stats_html

# =========================
# GENERAR HTML PROFESIONAL CON PESTAÑAS Y MENÚ
# =========================
def generar_html(rankings_por_carrera: List[pd.DataFrame], ranking_acumulado: pd.DataFrame, 
                 grafico_barras: str, grafico_evolucion: str, grafico_pastel: str, 
                 stats_adicionales: str) -> str:
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Ranking F1 Predicciones - Temporada 2025</title>
        <style>
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                background-color: #1A1A1A;
                color: #FFFFFF;
                margin: 0;
                padding: 0;
                line-height: 1.6;
            }}
            header {{
                background-color: #E10600;
                padding: 20px;
                text-align: center;
            }}
            header h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            nav {{
                background-color: #000000;
                padding: 10px;
            }}
            nav ul {{
                list-style: none;
                padding: 0;
                margin: 0;
                display: flex;
                justify-content: center;
            }}
            nav li {{
                margin: 0 15px;
            }}
            nav a {{
                color: #FFFFFF;
                text-decoration: none;
                font-weight: bold;
            }}
            nav a:hover {{
                color: #E10600;
            }}
            .tab-container {{
                max-width: 1200px;
                margin: 20px auto;
            }}
            .tab-buttons {{
                display: flex;
                border-bottom: 2px solid #333;
            }}
            .tab-button {{
                background-color: #333;
                border: none;
                color: #FFF;
                padding: 15px 20px;
                cursor: pointer;
                font-size: 1em;
                transition: background 0.3s;
                flex: 1;
            }}
            .tab-button:hover, .tab-button.active {{
                background-color: #E10600;
            }}
            .tab-content {{
                display: none;
                padding: 20px;
                background-color: #222;
                border-radius: 0 0 8px 8px;
            }}
            .tab-content.active {{
                display: block;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #444;
                padding: 12px;
                text-align: left;
            }}
            th {{
                background-color: #E10600;
            }}
            tr:nth-child(even) {{
                background-color: #333;
            }}
            tr:hover {{
                background-color: #444;
            }}
            .chart-container {{
                text-align: center;
                margin: 20px 0;
            }}
            .chart-container img {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            .stats-container {{
                background-color: #333;
                padding: 20px;
                border-radius: 8px;
            }}
            .stats-container ul {{
                list-style: none;
                padding: 0;
            }}
            .stats-container li {{
                margin-bottom: 10px;
            }}
            .accordion {{
                margin-bottom: 20px;
            }}
            .accordion-button {{
                background-color: #333;
                color: #FFF;
                padding: 15px;
                width: 100%;
                text-align: left;
                border: none;
                cursor: pointer;
                font-size: 1.1em;
                transition: background 0.3s;
            }}
            .accordion-button:hover {{
                background-color: #444;
            }}
            .accordion-content {{
                display: none;
                padding: 15px;
                background-color: #222;
            }}
            footer {{
                text-align: center;
                padding: 10px;
                background-color: #000;
                margin-top: 20px;
            }}
        </style>
        <script>
            function openTab(evt, tabName) {{
                var i, tabcontent, tabbuttons;
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {{
                    tabcontent[i].classList.remove("active");
                }}
                tabbuttons = document.getElementsByClassName("tab-button");
                for (i = 0; i < tabbuttons.length; i++) {{
                    tabbuttons[i].classList.remove("active");
                }}
                document.getElementById(tabName).classList.add("active");
                evt.currentTarget.classList.add("active");
            }}
            function toggleAccordion(id) {{
                var content = document.getElementById(id);
                if (content.style.display === "block") {{
                    content.style.display = "none";
                }} else {{
                    content.style.display = "block";
                }}
            }}
        </script>
    </head>
    <body>
        <header>
            <h1>🏁 Ranking de Predicciones F1 - Temporada 2025</h1>
        </header>
        <nav>
            <ul>
                <li><a href="#acumulado" onclick="document.querySelector('.tab-button[onclick*=\\'acumulado\\']').click();">Acumulado</a></li>
                <li><a href="#por-carrera" onclick="document.querySelector('.tab-button[onclick*=\\'por-carrera\\']').click();">Por Carrera</a></li>
                <li><a href="#graficos" onclick="document.querySelector('.tab-button[onclick*=\\'graficos\\']').click();">Gráficos</a></li>
                <li><a href="#estadisticas" onclick="document.querySelector('.tab-button[onclick*=\\'estadisticas\\']').click();">Estadísticas</a></li>
            </ul>
        </nav>
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="openTab(event, 'acumulado')">Ranking Acumulado</button>
                <button class="tab-button" onclick="openTab(event, 'por-carrera')">Rankings por Carrera</button>
                <button class="tab-button" onclick="openTab(event, 'graficos')">Gráficos</button>
                <button class="tab-button" onclick="openTab(event, 'estadisticas')">Estadísticas</button>
            </div>
            
            <div id="acumulado" class="tab-content active">
                <h2>Ranking Acumulado General</h2>
                {ranking_acumulado_html}
                <div class="chart-container">
                    <h3>Gráfico de Puntos Acumulados</h3>
                    <img src="data:image/png;base64,{grafico_barras}" alt="Gráfico de Barras Acumulado">
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
                    <img src="data:image/png;base64,{grafico_evolucion}" alt="Gráfico de Evolución">
                </div>
                <div class="chart-container">
                    <h3>Participación por Carrera</h3>
                    <img src="data:image/png;base64,{grafico_pastel}" alt="Gráfico de Pastel Participación">
                </div>
            </div>
            
            <div id="estadisticas" class="tab-content">
                <h2>Estadísticas Adicionales</h2>
                {stats_adicionales}
            </div>
        </div>
        <footer>
            <p>Generado automáticamente - {fecha_actual}</p>
        </footer>
    </body>
    </html>
    """
    
    # Insertar contenidos
    ranking_acumulado_html = ranking_acumulado.to_html(index=False, classes="ranking-table", escape=False) if not ranking_acumulado.empty else "<p>No hay datos disponibles.</p>"  # escape=False para HTML en Cambio
    
    rankings_por_carrera_html = ""
    for i, ranking in enumerate(rankings_por_carrera):
        carrera = ranking["Carrera"].iloc[0]
        ranking_table = ranking.drop(columns=["Carrera", "Detalles"]).to_html(index=False, classes="ranking-table")
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
    
    from datetime import datetime
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    
    return html.format(
        ranking_acumulado_html=ranking_acumulado_html,
        rankings_por_carrera_html=rankings_por_carrera_html,
        grafico_barras=grafico_barras,
        grafico_evolucion=grafico_evolucion,
        grafico_pastel=grafico_pastel,
        stats_adicionales=stats_adicionales,
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
                all_rankings = pd.concat([all_rankings, ranking.drop(columns=["Detalles"])])  # Sin detalles para acumulado
                all_dfs.append(df)
            else:
                print(f"Advertencia: No hay resultados reales completos para {nombre_carrera}")
    
    # Calcular acumulado (sin detalles, ya que son por carrera)
    if not all_rankings.empty:
        ranking_acumulado = (
            all_rankings.groupby("Dirección de correo electrónico", as_index=False)["Puntos"]
            .sum()
            .sort_values("Puntos", ascending=False)
            .reset_index(drop=True)
        )
        ranking_acumulado["Posición"] = ranking_acumulado.index + 1
        ranking_acumulado = ranking_acumulado[["Posición", "Dirección de correo electrónico", "Puntos"]]
        ranking_acumulado = calcular_cambios_posiciones(all_rankings, ranking_acumulado)  # Llamada corregida
    else:
        ranking_acumulado = pd.DataFrame(columns=["Posición", "Dirección de correo electrónico", "Puntos", "Cambio"])
    
    # Generar gráficos
    grafico_barras = generar_grafico_barras_acumulado(ranking_acumulado)
    grafico_evolucion = generar_grafico_evolucion(all_rankings)
    grafico_pastel = generar_grafico_pastel_participacion(all_dfs)
    
    # Estadísticas
    stats_adicionales = generar_estadisticas_adicionales(all_dfs, ranking_acumulado)
    
    # Generar HTML
    html_content = generar_html(rankings_por_carrera, ranking_acumulado, 
                                grafico_barras, grafico_evolucion, grafico_pastel, 
                                stats_adicionales)
    with open("ranking_f1.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("🏁 HTML generado: ranking_f1.html")
    print("Ábrelo en un navegador para ver el ranking profesional con pestañas, menús y gráficos.")

if __name__ == "__main__":
    main()