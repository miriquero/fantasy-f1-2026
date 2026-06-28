import pandas as pd
import os
import json
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime, timezone, timedelta
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

# =========================
# BADGES META (sistema de logros completo)
# =========================
BADGES_META = {
    "francotirador":   {"emoji":"🎯","nombre":"Francotirador",    "nivel":"BRONCE",    "nivel_emoji":"🥉","hex":"#E74C3C","desc_corta":"Acertar P1 exacto en 5 carreras distintas","desc_larga":"No tienen que ser seguidas. Pero acertar 5 ganadores en 22 carreras requiere leer bien hasta las fechas más impredecibles.","progreso_max":5},
    "racha_caliente":  {"emoji":"🔥","nombre":"Racha Caliente",   "nivel":"BRONCE",    "nivel_emoji":"🥉","hex":"#E67E22","desc_corta":"Top-3 del grupo en 3 carreras consecutivas","desc_larga":"Sostener el nivel sin un solo tropiezo durante tres fechas seguidas. La consistencia a corto plazo tiene su recompensa.","progreso_max":3},
    "hincha_franco":   {"emoji":"🇦🇷","nombre":"Hincha de Franco","nivel":"BRONCE",    "nivel_emoji":"🥉","hex":"#3498DB","desc_corta":"Posición exacta de Colapinto en 4 carreras","desc_larga":"Con su variabilidad de resultados, acertar 4 posiciones exactas de Franco Colapinto es una hazaña real.","progreso_max":4},
    "bomba_puntos":    {"emoji":"💣","nombre":"Bomba de Puntos",  "nivel":"BRONCE",    "nivel_emoji":"🥉","hex":"#C0392B","desc_corta":"Top-1 absoluto en puntaje en 4 carreras distintas","desc_larga":"Ganar una fecha es suerte. Ganar cuatro en la temporada es dominio real. Sin empates, techo absoluto del grupo.","progreso_max":4},
    "adivino":         {"emoji":"🔮","nombre":"Adivino",          "nivel":"BRONCE",    "nivel_emoji":"🥉","hex":"#9B59B6","desc_corta":"5+ aciertos exactos en una sola carrera","desc_larga":"Acertar la mitad exacta de las 10 posiciones predichas es estadísticamente raro con 20 pilotos en pista.","progreso_max":5},
    "muralla":         {"emoji":"🛡️","nombre":"Muralla",          "nivel":"PLATA",     "nivel_emoji":"🥈","hex":"#95A5A6","desc_corta":"Nunca terminar último en el ranking de ninguna carrera","desc_larga":"Con 10-12 jugadores, evitar el fondo absoluto durante toda la temporada es un logro de consistencia pura.","progreso_max":22},
    "remontada_epica": {"emoji":"📈","nombre":"Remontada Épica",  "nivel":"PLATA",     "nivel_emoji":"🥈","hex":"#27AE60","desc_corta":"De los últimos 3 del ranking a top-3 en 4 fechas","desc_larga":"La remontada tiene que ser profunda (desde el fondo) y sostenida (mantenerse 4 fechas consecutivas en el top).","progreso_max":1},
    "estratega":       {"emoji":"🧠","nombre":"Estratega",        "nivel":"PLATA",     "nivel_emoji":"🥈","hex":"#16A085","desc_corta":"Top-5 completo exacto (P1-P5 en orden) en una carrera","desc_larga":"Cinco posiciones exactas de diez en una carrera de F1. Brutal. La probabilidad estadística es mínima.","progreso_max":1},
    "consistente":     {"emoji":"⚙️","nombre":"Consistente",      "nivel":"PLATA",     "nivel_emoji":"🥈","hex":"#7F8C8D","desc_corta":"Top-50% del grupo en 17 de las 22 carreras","desc_larga":"Solo 5 fechas malas permitidas en toda la temporada. No hay margen para rachas negativas prolongadas.","progreso_max":17},
    "apostador_nato":  {"emoji":"🎰","nombre":"Apostador Nato",   "nivel":"PLATA",     "nivel_emoji":"🥈","hex":"#8E44AD","desc_corta":"Acierto exacto entre P7-P10 en 6 carreras distintas","desc_larga":"La zona del caos total. Acertar 6 posiciones exactas entre P7 y P10 a lo largo de la temporada es excepcional.","progreso_max":6},
    "marea_alta":      {"emoji":"🌊","nombre":"Marea Alta",       "nivel":"ORO",       "nivel_emoji":"🥇","hex":"#2471A3","desc_corta":"Top-1 del grupo en 7 o más carreras individuales","desc_larga":"Una de cada tres carreras tiene que ser tuya. Ganar el ranking general y este badge a la vez es rarísimo.","progreso_max":7},
    "arquitecto":      {"emoji":"🏗️","nombre":"Arquitecto",       "nivel":"ORO",       "nivel_emoji":"🥇","hex":"#D35400","desc_corta":"Mayor puntaje acumulado en predicciones P6-P10","desc_larga":"Premia el conocimiento profundo del pelotón medio, no solo adivinar a los favoritos de siempre.","progreso_max":1},
    "oraculo":         {"emoji":"🌌","nombre":"Oráculo",          "nivel":"LEGENDARIO","nivel_emoji":"💎","hex":"#4A90E2","desc_corta":"Podio exacto (P1, P2 y P3) en 5 carreras distintas","desc_larga":"El podio exacto cinco veces. La probabilidad estadística de lograrlo en una sola carrera ya es ridículamente baja.","progreso_max":5},
    "perfeccionista":  {"emoji":"💎","nombre":"Perfeccionista",   "nivel":"LEGENDARIO","nivel_emoji":"💎","hex":"#00BCD4","desc_corta":"7+ aciertos exactos en una sola carrera","desc_larga":"Casi imposible. Si alguien lo logra en alguna fecha, es el momento de la temporada. Estadísticamente brutal.","progreso_max":7},
    "rey_temporada":   {"emoji":"👑","nombre":"Rey de la Temporada","nivel":"CAMPEÓN", "nivel_emoji":"🏆","hex":"#F39C12","desc_corta":"Primero en el ranking general al cierre de la temporada","desc_larga":"El logro más grande del torneo. Solo uno puede tenerlo por temporada. No hay nada por encima de este badge.","progreso_max":1},
}

NIVEL_CONFIG = {
    "BRONCE":    {"color": "#CD7F32", "bg": "rgba(205,127,50,0.08)",  "border": "rgba(205,127,50,0.25)",  "label": "🥉 BRONCE",    "order": 1},
    "PLATA":     {"color": "#C0C0C0", "bg": "rgba(192,192,192,0.08)", "border": "rgba(192,192,192,0.25)", "label": "🥈 PLATA",     "order": 2},
    "ORO":       {"color": "#FFD700", "bg": "rgba(255,215,0,0.08)",   "border": "rgba(255,215,0,0.3)",    "label": "🥇 ORO",       "order": 3},
    "LEGENDARIO":{"color": "#4A90E2", "bg": "rgba(74,144,226,0.08)",  "border": "rgba(74,144,226,0.3)",   "label": "💎 LEGENDARIO","order": 4},
    "CAMPEÓN":   {"color": "#F39C12", "bg": "rgba(243,156,18,0.08)",  "border": "rgba(243,156,18,0.3)",   "label": "🏆 CAMPEÓN",   "order": 5},
}

BADGES_DEF = {
    "francotirador":  {
        "emoji": "🎯", "nombre": "Francotirador",    "hex": "#E74C3C",
        "nivel": "BRONCE",    "nivel_emoji": "🥉",
        "criterio": "Acertar la posición exacta del ganador (P1) en 5 o más carreras de la temporada."
    },
    "racha_caliente": {
        "emoji": "🔥", "nombre": "Racha Caliente",   "hex": "#E67E22",
        "nivel": "BRONCE",    "nivel_emoji": "🥉",
        "criterio": "Terminar en el top-3 del ranking grupal en 4 carreras consecutivas."
    },
    "hincha_franco":  {
        "emoji": "🇦🇷", "nombre": "Hincha de Franco", "hex": "#3498DB",
        "nivel": "BRONCE",    "nivel_emoji": "🥉",
        "criterio": "Acertar la posición exacta de Franco Colapinto en 4 o más carreras."
    },
    "bomba_puntos":   {
        "emoji": "💣", "nombre": "Bomba de Puntos",  "hex": "#C0392B",
        "nivel": "BRONCE",    "nivel_emoji": "🥉",
        "criterio": "Ser el máximo anotador individual del grupo en 3 o más carreras distintas."
    },
    "adivino":        {
        "emoji": "🔮", "nombre": "Adivino",          "hex": "#9B59B6",
        "nivel": "BRONCE",    "nivel_emoji": "🥉",
        "criterio": "Lograr 6 o más predicciones de posición exacta en una misma carrera."
    },
    "muralla":        {
        "emoji": "🛡️", "nombre": "Muralla",          "hex": "#95A5A6",
        "nivel": "PLATA",     "nivel_emoji": "🥈",
        "criterio": "No terminar nunca último en el ranking individual de ninguna carrera disputada."
    },
    "remontada_epica":{
        "emoji": "📈", "nombre": "Remontada Épica",  "hex": "#27AE60",
        "nivel": "PLATA",     "nivel_emoji": "🥈",
        "criterio": "Pasar de los últimos 3 del ranking general a top-2 y sostenerlo 4 fechas seguidas."
    },
    "estratega":      {
        "emoji": "🧠", "nombre": "Estratega",        "hex": "#16A085",
        "nivel": "PLATA",     "nivel_emoji": "🥈",
        "criterio": "Acertar P1, P2, P3, P4 y P5 exactos en orden en una misma carrera."
    },
    "consistente":    {
        "emoji": "⚙️", "nombre": "Consistente",      "hex": "#7F8C8D",
        "nivel": "PLATA",     "nivel_emoji": "🥈",
        "criterio": "Terminar en el top-50% del grupo en al menos 17 de las 22 carreras."
    },
    "apostador_nato": {
        "emoji": "🎰", "nombre": "Apostador Nato",   "hex": "#8E44AD",
        "nivel": "PLATA",     "nivel_emoji": "🥈",
        "criterio": "Acertar una posición exacta entre P7 y P10 en 6 o más carreras distintas."
    },
    "rey_temporada":  {
        "emoji": "👑", "nombre": "Rey de la Temporada","hex": "#F39C12",
        "nivel": "ORO",       "nivel_emoji": "🥇",
        "criterio": "Liderar el ranking general acumulado al cierre de la temporada."
    },
    "marea_alta":     {
        "emoji": "🌊", "nombre": "Marea Alta",       "hex": "#2471A3",
        "nivel": "ORO",       "nivel_emoji": "🥇",
        "criterio": "Ser el top-1 del grupo en el puntaje individual de 7 o más carreras."
    },
    "arquitecto":     {
        "emoji": "🏗️", "nombre": "Arquitecto",       "hex": "#D35400",
        "nivel": "ORO",       "nivel_emoji": "🥇",
        "criterio": "Tener el mayor puntaje acumulado del grupo en predicciones de P6 a P10."
    },
    "oraculo":        {
        "emoji": "🌌", "nombre": "Oráculo",          "hex": "#4A90E2",
        "nivel": "LEGENDARIO","nivel_emoji": "💎",
        "criterio": "Acertar el podio completo (P1, P2 y P3 en orden exacto) en 4 o más carreras."
    },
    "perfeccionista": {
        "emoji": "💎", "nombre": "Perfeccionista",   "hex": "#00BCD4",
        "nivel": "LEGENDARIO","nivel_emoji": "💎",
        "criterio": "Lograr 7 o más predicciones de posición exacta en una misma carrera."
    },
}

def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

hex_to_rgba_logros = hex_to_rgba

# =========================
# CALENDARIO
# =========================
CALENDARIO = [
    {"Jornada": "R01", "Carrera": "AUSTRALIA",      "Fecha": "8 MAR",   "Hora Local": "15:00", "Hora Argentina": "01:00",              "FechaISO": "2026-03-08T01:00:00-03:00"},
    {"Jornada": "R02", "Carrera": "CHINA",           "Fecha": "15 MAR",  "Hora Local": "15:00", "Hora Argentina": "04:00",              "FechaISO": "2026-03-15T04:00:00-03:00"},
    {"Jornada": "R03", "Carrera": "JAPON",           "Fecha": "29 MAR",  "Hora Local": "14:00", "Hora Argentina": "02:00",              "FechaISO": "2026-03-29T02:00:00-03:00"},
    {"Jornada": "<s>R04</s>", "Carrera": "<s>BAHREIN</s>",        "Fecha": "<s>12 ABR</s>", "Hora Local": "<s>18:00</s>", "Hora Argentina": "<s>12:00</s>", "FechaISO": None},
    {"Jornada": "<s>R05</s>", "Carrera": "<s>ARABIA SAUDITA</s>", "Fecha": "<s>19 ABR</s>", "Hora Local": "<s>20:00</s>", "Hora Argentina": "<s>14:00</s>", "FechaISO": None},
    {"Jornada": "R06", "Carrera": "MIAMI",          "Fecha": "03 MAY",  "Hora Local": "16:00", "Hora Argentina": "17:00",              "FechaISO": "2026-05-03T17:00:00-03:00"},
    {"Jornada": "R07", "Carrera": "CANADA",         "Fecha": "24 MAY",  "Hora Local": "16:00", "Hora Argentina": "17:00",              "FechaISO": "2026-05-24T17:00:00-03:00"},
    {"Jornada": "R08", "Carrera": "MONACO",         "Fecha": "07 JUN",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-06-07T10:00:00-03:00"},
    {"Jornada": "R09", "Carrera": "BARCELONA",      "Fecha": "14 JUN",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-06-14T10:00:00-03:00"},
    {"Jornada": "R10", "Carrera": "AUSTRIA",        "Fecha": "28 JUN",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-06-28T10:00:00-03:00"},
    {"Jornada": "R11", "Carrera": "GRAN BRETAÑA",   "Fecha": "05 JUL",  "Hora Local": "15:00", "Hora Argentina": "11:00",              "FechaISO": "2026-07-05T11:00:00-03:00"},
    {"Jornada": "R12", "Carrera": "BÉLGICA",        "Fecha": "19 JUL",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-07-19T10:00:00-03:00"},
    {"Jornada": "R13", "Carrera": "HUNGRÍA",        "Fecha": "26 JUL",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-07-26T10:00:00-03:00"},
    {"Jornada": "R14", "Carrera": "PAÍSES BAJOS",   "Fecha": "23 AGO",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-08-23T10:00:00-03:00"},
    {"Jornada": "R15", "Carrera": "ITALIA",         "Fecha": "06 SEP",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-09-06T10:00:00-03:00"},
    {"Jornada": "R16", "Carrera": "MADRID",         "Fecha": "13 SEP",  "Hora Local": "15:00", "Hora Argentina": "10:00",              "FechaISO": "2026-09-13T10:00:00-03:00"},
    {"Jornada": "R17", "Carrera": "AZERBAIYN",      "Fecha": "26 SEP",  "Hora Local": "15:00", "Hora Argentina": "08:00",              "FechaISO": "2026-09-26T08:00:00-03:00"},
    {"Jornada": "R18", "Carrera": "SINGAPUR",       "Fecha": "11 OCT",  "Hora Local": "20:00", "Hora Argentina": "09:00",              "FechaISO": "2026-10-11T09:00:00-03:00"},
    {"Jornada": "R19", "Carrera": "AUSTIN",         "Fecha": "25 OCT",  "Hora Local": "15:00", "Hora Argentina": "17:00",              "FechaISO": "2026-10-25T17:00:00-03:00"},
    {"Jornada": "R20", "Carrera": "MEXICO",         "Fecha": "01 NOV",  "Hora Local": "14:00", "Hora Argentina": "17:00",              "FechaISO": "2026-11-01T17:00:00-03:00"},
    {"Jornada": "R21", "Carrera": "BRASIL",         "Fecha": "08 NOV",  "Hora Local": "14:00", "Hora Argentina": "14:00",              "FechaISO": "2026-11-08T14:00:00-03:00"},
    {"Jornada": "R22", "Carrera": "LAS VEGAS",      "Fecha": "21 NOV",  "Hora Local": "20:00", "Hora Argentina": "01:00 (Dom 22)", "FechaISO": "2026-11-22T01:00:00-03:00"},
    {"Jornada": "R23", "Carrera": "QATAR",          "Fecha": "29 NOV",  "Hora Local": "19:00", "Hora Argentina": "13:00",              "FechaISO": "2026-11-29T13:00:00-03:00"},
    {"Jornada": "R24", "Carrera": "ABU DHABI",      "Fecha": "06 DIC",  "Hora Local": "17:00", "Hora Argentina": "10:00",              "FechaISO": "2026-12-06T10:00:00-03:00"},
]

COLORES_PARTICIPANTES = ['#E10600','#00C8FF','#FFD700','#C77DFF','#39FF14','#FF6B35','#00E5CC','#FF69B4']

FLAG_MAP = {
    "Australia": "🇦🇺", "China": "🇨🇳", "Japon": "🇯🇵", "Bahrein": "🇧🇭",
    "Arabia saudita": "🇸🇦", "Miami": "🇺🇸", "Canada": "🇨🇦", "Mónaco": "🇲🇨",
    "Monaco": "🇲🇨", "Barcelona": "🇪🇸", "Austria": "🇦🇹", "Gran bretaña": "🇬🇧",
    "Gran bretana": "🇬🇧", "Bélgica": "🇧🇪", "Belgica": "🇧🇪", "Hungría": "🇭🇺",
    "Hungria": "🇭🇺", "Países bajos": "🇳🇱", "Paises bajos": "🇳🇱", "Italia": "🇮🇹",
    "Madrid": "🇪🇸", "Azerbaiyn": "🇦🇿", "Singapur": "🇸🇬", "Austin": "🇺🇸",
    "Mexico": "🇲🇽", "Brasil": "🇧🇷", "Las vegas": "🇺🇸", "Qatar": "🇶🇦",
    "Abu dhabi": "🇦🇪",
}

def get_orden_carreras() -> List[str]:
    orden = []
    for entry in CALENDARIO:
        nombre_raw = entry["Carrera"]
        if "<s>" in nombre_raw:
            continue
        nombre = re.sub(r'<[^>]+>', '', nombre_raw).strip().capitalize()
        if nombre not in orden:
            orden.append(nombre)
    return orden

def carreras_en_orden(available: List[str]) -> List[str]:
    orden_cal = get_orden_carreras()
    available_set = set(available)
    ordenadas = [c for c in orden_cal if c in available_set]
    for c in available:
        if c not in ordenadas:
            ordenadas.append(c)
    return ordenadas

def puntos_posicion(predicha: int, real: int) -> int:
    if predicha == real:
        return 10
    elif abs(predicha - real) == 1:
        return 5
    else:
        return 1

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

def calcular_cambios_posiciones(all_rankings: pd.DataFrame, ranking_acumulado: pd.DataFrame) -> pd.DataFrame:
    if len(all_rankings['Carrera'].unique()) < 2:
        ranking_acumulado['Cambio'] = '-'
        return ranking_acumulado
    carreras = carreras_en_orden(all_rankings['Carrera'].unique().tolist())
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
        pos_prev = acum_prev.get(email, None)
        if pos_prev is None or not np.isfinite(pos_prev):
            cambios[email] = '<span class="trend-neutral">—</span>'
            continue
        diff = pos_prev - pos_actual
        if diff > 0:
            cambios[email] = f'<span class="trend-up">▲{int(diff)}</span>'
        elif diff < 0:
            cambios[email] = f'<span class="trend-down">▼{int(-diff)}</span>'
        else:
            cambios[email] = '<span class="trend-neutral">—</span>'
    ranking_acumulado['Cambio'] = ranking_acumulado['Dirección de correo electrónico'].map(cambios)
    return ranking_acumulado

def calcular_historial_posiciones(all_rankings: pd.DataFrame) -> pd.DataFrame:
    if all_rankings.empty:
        return pd.DataFrame()
    carreras = carreras_en_orden(all_rankings['Carrera'].unique().tolist())
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
# CALCULAR BADGES / LOGROS
# =========================
def calcular_pts_p6_p10(detalles_str: str) -> int:
    total = 0
    for line in detalles_str.split('<br>'):
        for pos in range(6, 11):
            if f'Exacto en P{pos}' in line:
                total += 10; break
            elif f'pred P{pos},' in line:
                if '+5' in line:   total += 5
                elif '+1' in line: total += 1
                break
    return total


def calcular_badges(all_rankings: pd.DataFrame, all_dfs: List[pd.DataFrame],
                    ranking_acumulado: pd.DataFrame) -> Dict[str, List[Dict]]:
    if all_rankings.empty or ranking_acumulado.empty:
        return {}

    df_all = pd.concat(all_dfs) if all_dfs else pd.DataFrame()
    historial  = calcular_historial_posiciones(all_rankings)
    carreras   = carreras_en_orden(all_rankings['Carrera'].unique().tolist())
    n_part     = ranking_acumulado.shape[0]
    n_disp     = len(carreras)

    per_race_pos: Dict[str, Dict[str, int]] = {}
    for _, row in all_rankings.iterrows():
        em = row['Dirección de correo electrónico']
        per_race_pos.setdefault(em, {})[row['Carrera']] = int(row['Posición'])

    n_part_per_race: Dict[str, int] = {
        c: int(all_rankings[all_rankings['Carrera'] == c]['Dirección de correo electrónico'].nunique())
        for c in carreras
    }

    cumul_pos: Dict[str, Dict[str, int]] = {}
    if not historial.empty:
        for _, row in historial.iterrows():
            em = row['Dirección de correo electrónico']
            cumul_pos.setdefault(em, {})[row['Carrera']] = int(row['Posición'])

    top1_per_race: Dict[str, List[str]] = {}
    for c in carreras:
        sub = all_rankings[all_rankings['Carrera'] == c]
        if not sub.empty:
            mx = sub['Puntos'].max()
            top1_per_race[c] = sub[sub['Puntos'] == mx]['Dirección de correo electrónico'].tolist()

    arch_pts: Dict[str, int] = {
        em: sum(
            calcular_pts_p6_p10(str(r['Detalles']))
            for _, r in df_all[df_all['Dirección de correo electrónico'] == em].iterrows()
        )
        for em in ranking_acumulado['Dirección de correo electrónico']
    } if not df_all.empty else {}
    max_arch = max(arch_pts.values(), default=0)

    badges_resultado: Dict[str, List[Dict]] = {}

    for _, acum_row in ranking_acumulado.iterrows():
        email    = acum_row['Dirección de correo electrónico']
        pos_gral = int(acum_row['Posición'])
        badges: List[Dict] = []

        part_df = df_all[df_all['Dirección de correo electrónico'] == email] \
                  if not df_all.empty else pd.DataFrame()
        my_rp   = per_race_pos.get(email, {})
        my_cp   = cumul_pos.get(email, {})

        def exactos_en_fila(det: str) -> int:
            return sum(1 for d in str(det).split('<br>') if 'Exacto en P' in d)

        # 🎯 FRANCOTIRADOR
        p1_ok = sum(1 for _, r in part_df.iterrows() if 'Exacto en P1' in str(r['Detalles']))
        if p1_ok >= 5:
            badges.append({**BADGES_DEF["francotirador"],
                "desc": (f"{BADGES_DEF['francotirador']['nivel_emoji']} BRONCE · "
                         f"Acertaste el ganador exacto en {p1_ok} carreras. "
                         f"Criterio: 5+ aciertos de P1 en la temporada.")})

        # 🔥 RACHA CALIENTE
        consec = max_consec = 0
        for c in carreras:
            p = my_rp.get(c)
            if p is not None and p <= 3:
                consec += 1; max_consec = max(max_consec, consec)
            else:
                consec = 0
        if max_consec >= 3:
            badges.append({**BADGES_DEF["racha_caliente"],
                "desc": (f"{BADGES_DEF['racha_caliente']['nivel_emoji']} BRONCE · "
                         f"Quedaste en el top-3 del grupo {max_consec} carreras seguidas. "
                         f"Criterio: 3+ fechas consecutivas en el podio grupal.")})

        # 🇦🇷 HINCHA DE FRANCO
        cola_ok = sum(1 for _, r in part_df.iterrows() if 'Colapinto: EXACTO' in str(r['Detalles']))
        if cola_ok >= 4:
            badges.append({**BADGES_DEF["hincha_franco"],
                "desc": (f"{BADGES_DEF['hincha_franco']['nivel_emoji']} BRONCE · "
                         f"Acertaste la posición exacta de Franco Colapinto en {cola_ok} carreras. "
                         f"Criterio: 4+ aciertos exactos.")})

        # 💣 BOMBA DE PUNTOS
        bomba_n = sum(1 for c in carreras if email in top1_per_race.get(c, []))
        if bomba_n >= 4:
            badges.append({**BADGES_DEF["bomba_puntos"],
                "desc": (f"{BADGES_DEF['bomba_puntos']['nivel_emoji']} BRONCE · "
                         f"Fuiste el máximo anotador del grupo en {bomba_n} carreras distintas. "
                         f"Criterio: 4+ victorias de fecha.")})

        # 🔮 ADIVINO
        adivino_max = adivino_carrera = 0
        for _, r in part_df.iterrows():
            ex = exactos_en_fila(r['Detalles'])
            if ex > adivino_max:
                adivino_max = ex; adivino_carrera = r['Carrera']
        if adivino_max >= 5:
            badges.append({**BADGES_DEF["adivino"],
                "desc": (f"{BADGES_DEF['adivino']['nivel_emoji']} BRONCE · "
                         f"Lograste {adivino_max} predicciones exactas en {adivino_carrera}. "
                         f"Criterio: 5+ aciertos exactos en una carrera (sobre 10).")})

        # 🛡️ MURALLA
        muralla = all(
            my_rp.get(c, 1) < n_part_per_race.get(c, n_part)
            for c in carreras
        ) and n_disp > 0
        if muralla:
            badges.append({**BADGES_DEF["muralla"],
                "desc": (f"{BADGES_DEF['muralla']['nivel_emoji']} PLATA · "
                         f"Nunca terminaste en el último lugar del ranking en ninguna "
                         f"de las {n_disp} carreras disputadas.")})

        # 📈 REMONTADA ÉPICA
        remontada_epica = False
        if len(carreras) >= 5:
            for i in range(len(carreras) - 4):
                pos_t = my_cp.get(carreras[i])
                if pos_t is None or pos_t < (n_part - 2):
                    continue
                siguientes = [my_cp.get(carreras[i + j + 1]) for j in range(4)]
                if all(p is not None and p <= 3 for p in siguientes):
                    remontada_epica = True; break
        if remontada_epica:
            badges.append({**BADGES_DEF["remontada_epica"],
                "desc": (f"{BADGES_DEF['remontada_epica']['nivel_emoji']} PLATA · "
                         f"Pasaste de estar en los últimos 3 del ranking general a top-3 y "
                         f"lo sostuviste 4 carreras seguidas.")})

        # 🧠 ESTRATEGA
        estratega_carrera = None
        for _, r in part_df.iterrows():
            if all(f'Exacto en P{p}' in str(r['Detalles']) for p in range(1, 6)):
                estratega_carrera = r['Carrera']; break
        if estratega_carrera:
            badges.append({**BADGES_DEF["estratega"],
                "desc": (f"{BADGES_DEF['estratega']['nivel_emoji']} PLATA · "
                         f"Acertaste P1, P2, P3, P4 y P5 exactos en orden en {estratega_carrera}. "
                         f"Cinco posiciones exactas de una. Brutal.")})

        # ⚙️ CONSISTENTE
        umbral_50 = n_part / 2
        top50_n = sum(1 for c in carreras if (my_rp.get(c) or 999) <= umbral_50)
        if top50_n >= 17:
            badges.append({**BADGES_DEF["consistente"],
                "desc": (f"{BADGES_DEF['consistente']['nivel_emoji']} PLATA · "
                         f"Terminaste en el top-50% del grupo en {top50_n} de las {n_disp} "
                         f"carreras disputadas. Criterio: 17+ fechas en la mitad superior.")})

        # 🎰 APOSTADOR NATO
        apuesta_carreras = set()
        for _, r in part_df.iterrows():
            det = str(r['Detalles'])
            if any(f'Exacto en P{p}' in det for p in range(7, 11)):
                apuesta_carreras.add(r['Carrera'])
        if len(apuesta_carreras) >= 6:
            badges.append({**BADGES_DEF["apostador_nato"],
                "desc": (f"{BADGES_DEF['apostador_nato']['nivel_emoji']} PLATA · "
                         f"Acertaste una posición exacta entre P7 y P10 en "
                         f"{len(apuesta_carreras)} carreras distintas. "
                         f"Criterio: 6+ carreras. La zona del caos total.")})

        # 🌊 MAREA ALTA
        marea_n = sum(1 for c in carreras if email in top1_per_race.get(c, []))
        if marea_n >= 7:
            badges.append({**BADGES_DEF["marea_alta"],
                "desc": (f"{BADGES_DEF['marea_alta']['nivel_emoji']} ORO · "
                         f"Fuiste el top-1 del grupo en {marea_n} carreras individuales. "
                         f"Criterio: 7+ victorias de fecha.")})

        # 🏗️ ARQUITECTO
        if arch_pts.get(email, 0) >= max_arch > 0:
            badges.append({**BADGES_DEF["arquitecto"],
                "desc": (f"{BADGES_DEF['arquitecto']['nivel_emoji']} ORO · "
                         f"Mayor puntaje del grupo en predicciones de P6 a P10: "
                         f"{arch_pts.get(email,0)} pts.")})

        # 🌌 ORÁCULO
        oraculo_n = sum(
            1 for _, r in part_df.iterrows()
            if all(f'Exacto en P{p}' in str(r['Detalles']) for p in range(1, 4))
        )
        if oraculo_n >= 5:
            badges.append({**BADGES_DEF["oraculo"],
                "desc": (f"{BADGES_DEF['oraculo']['nivel_emoji']} LEGENDARIO · "
                         f"Acertaste el podio completo (P1, P2 y P3 exactos en orden) en "
                         f"{oraculo_n} carreras. Criterio: 5+ carreras.")})

        # 💎 PERFECCIONISTA
        perf_max = perf_carrera = 0
        for _, r in part_df.iterrows():
            ex = exactos_en_fila(r['Detalles'])
            if ex > perf_max:
                perf_max = ex; perf_carrera = r['Carrera']
        if perf_max >= 7:
            badges.append({**BADGES_DEF["perfeccionista"],
                "desc": (f"{BADGES_DEF['perfeccionista']['nivel_emoji']} LEGENDARIO · "
                         f"Lograste {perf_max} predicciones exactas en {perf_carrera}. "
                         f"Criterio: 7+ aciertos exactos en una carrera.")})

        # 👑 REY DE LA TEMPORADA
        if pos_gral == 1:
            badges.append({**BADGES_DEF["rey_temporada"],
                "desc": (f"{BADGES_DEF['rey_temporada']['nivel_emoji']} CAMPEÓN · "
                         f"Líder del ranking general acumulado. "
                         f"El logro más grande del torneo. Solo uno puede tenerlo.")})

        badges_resultado[email] = badges

    return badges_resultado


# =========================
# PANEL DE LOGROS
# =========================
def generar_logros_panel_html(badges_por_participante: dict) -> str:
    ganadores_por_badge: dict = {k: [] for k in BADGES_META}
    for email, badges in badges_por_participante.items():
        nombre = email.split('@')[0]
        for b in badges:
            for key, meta in BADGES_META.items():
                if meta["nombre"] == b["nombre"]:
                    ganadores_por_badge[key].append(nombre)
                    break

    ranking_badges = sorted(
        [(email.split('@')[0], len(badges)) for email, badges in badges_por_participante.items()],
        key=lambda x: -x[1]
    )

    total_badges_posibles = len(BADGES_META)

    lideres_rows = ""
    COLORES_PART = ['#E10600','#00C8FF','#FFD700','#C77DFF','#39FF14','#FF6B35','#00E5CC','#FF69B4']
    for i, (nombre, n) in enumerate(ranking_badges):
        color = COLORES_PART[i % len(COLORES_PART)]
        pct = round(n / total_badges_posibles * 100)
        bar_width = max(4, pct)
        lideres_rows += f"""
        <div class="logros-lider-row">
            <div class="logros-lider-left">
                <span class="logros-lider-pos" style="color:{color};">#{i+1}</span>
                <span class="logros-lider-nombre" style="color:{color};">{nombre}</span>
            </div>
            <div class="logros-lider-bar-wrap">
                <div class="logros-lider-bar-fill" style="width:{bar_width}%;background:{color};"></div>
            </div>
            <div class="logros-lider-right">
                <span class="logros-lider-count">{n}</span>
                <span class="logros-lider-total">/{total_badges_posibles}</span>
            </div>
        </div>"""

    niveles_html = ""
    for nivel_key in ["BRONCE","PLATA","ORO","LEGENDARIO","CAMPEÓN"]:
        nc = NIVEL_CONFIG[nivel_key]
        badges_del_nivel = {k: v for k, v in BADGES_META.items() if v["nivel"] == nivel_key}

        cards_html = ""
        for badge_key, meta in badges_del_nivel.items():
            ganadores = ganadores_por_badge.get(badge_key, [])
            desbloqueado = len(ganadores) > 0
            hex_color = meta["hex"]

            bg_card   = hex_to_rgba_logros(hex_color, 0.07 if desbloqueado else 0.03)
            border_c  = hex_to_rgba_logros(hex_color, 0.35 if desbloqueado else 0.12)
            emoji_bg  = hex_to_rgba_logros(hex_color, 0.15 if desbloqueado else 0.06)
            text_col  = hex_color if desbloqueado else "#444444"
            name_col  = "#FFFFFF" if desbloqueado else "#555555"
            desc_col  = "#AAAAAA" if desbloqueado else "#444444"
            long_col  = "#888888" if desbloqueado else "#333333"
            lock_icon = "" if desbloqueado else '<span class="badge-lock">🔒</span>'

            ganadores_html = ""
            if ganadores:
                ganadores_html = '<div class="badge-ganadores">'
                for g in ganadores:
                    ganadores_html += f'<span class="badge-ganador-chip">{g}</span>'
                ganadores_html += '</div>'
            else:
                ganadores_html = '<div class="badge-ganadores"><span class="badge-nadie">Sin desbloquear aún</span></div>'

            cards_html += f"""
            <div class="logro-card {'logro-desbloqueado' if desbloqueado else 'logro-bloqueado'}"
                 style="background:{bg_card};border:1px solid {border_c};">
                {lock_icon}
                <div class="logro-emoji-wrap" style="background:{emoji_bg};border:1px solid {border_c};">
                    <span class="logro-emoji">{meta['emoji']}</span>
                </div>
                <div class="logro-content">
                    <div class="logro-nombre" style="color:{name_col};">{meta['nombre']}</div>
                    <div class="logro-desc-corta" style="color:{text_col};">{meta['desc_corta']}</div>
                    <div class="logro-desc-larga" style="color:{long_col};">{meta['desc_larga']}</div>
                    {ganadores_html}
                </div>
            </div>"""

        niveles_html += f"""
        <div class="logros-nivel-block">
            <div class="logros-nivel-header" style="border-left:3px solid {nc['color']};">
                <span class="logros-nivel-label" style="color:{nc['color']};">{nc['label']}</span>
                <span class="logros-nivel-sub">
                    {sum(1 for k in badges_del_nivel if ganadores_por_badge.get(k))} / {len(badges_del_nivel)} desbloqueados
                </span>
            </div>
            <div class="logros-cards-grid">
                {cards_html}
            </div>
        </div>"""

    total_otorgados = sum(len(v) for v in ganadores_por_badge.values())
    total_unicos    = sum(1 for v in ganadores_por_badge.values() if v)

    leyenda_niveles = "".join(f'''<div class="logros-leyenda-row">
        <span class="logros-leyenda-dot" style="background:{NIVEL_CONFIG[n]["color"]};box-shadow:0 0 8px {NIVEL_CONFIG[n]["color"]}44;"></span>
        <span class="logros-leyenda-label" style="color:{NIVEL_CONFIG[n]["color"]};">{NIVEL_CONFIG[n]["label"]}</span>
    </div>''' for n in ["BRONCE","PLATA","ORO","LEGENDARIO","CAMPEÓN"])

    return f"""
<div id="panel-logros" class="tab-panel">
    <div class="logros-hero">
        <div class="logros-hero-bg"></div>
        <div class="logros-hero-content">
            <div class="logros-eyebrow">Sistema de Logros</div>
            <h2 class="logros-title">HAL<span>L OF</span><br>FAME</h2>
            <p class="logros-subtitle">15 badges · 5 niveles · 22 carreras · Solo los mejores los desbloquean</p>
            <div class="logros-hero-stats">
                <div class="logros-hero-stat">
                    <span class="logros-hero-num">{total_otorgados}</span>
                    <span class="logros-hero-desc">Badges otorgados</span>
                </div>
                <div class="logros-hero-divider"></div>
                <div class="logros-hero-stat">
                    <span class="logros-hero-num">{total_unicos}</span>
                    <span class="logros-hero-desc">Badges desbloqueados</span>
                </div>
                <div class="logros-hero-divider"></div>
                <div class="logros-hero-stat">
                    <span class="logros-hero-num">{total_badges_posibles}</span>
                    <span class="logros-hero-desc">Total disponibles</span>
                </div>
            </div>
        </div>
    </div>

    <div class="logros-main-grid">
        <div class="logros-sidebar">
            <div class="logros-sidebar-inner">
                <div class="logros-sidebar-title">🏆 Ranking de Logros</div>
                <div class="logros-sidebar-sub">Quién tiene más badges desbloqueados</div>
                <div class="logros-lideres-list">
                    {lideres_rows}
                </div>
                <div class="logros-leyenda">
                    <div class="logros-sidebar-title" style="margin-top:0;">Niveles de dificultad</div>
                    {leyenda_niveles}
                </div>
            </div>
        </div>
        <div class="logros-catalogo">
            {niveles_html}
        </div>
    </div>
</div>"""


LOGROS_CSS = """
/* ═══════════════════ LOGROS TAB ═══════════════════ */
.logros-hero {
    position: relative; overflow: hidden;
    border-radius: 16px; margin-bottom: 32px;
    min-height: 220px;
    border: 1px solid rgba(255,255,255,0.07);
    display: flex; align-items: flex-end;
}
.logros-hero-bg {
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse 80% 80% at 110% 50%, rgba(225,6,0,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 60% at -10% 100%, rgba(255,215,0,0.08) 0%, transparent 55%),
        linear-gradient(135deg, #0D0D0D 0%, #111111 100%);
    z-index: 0;
}
.logros-hero-bg::after {
    content: '🏆';
    position: absolute; right: 5%; top: 50%; transform: translateY(-50%);
    font-size: clamp(60px, 14vw, 160px);
    opacity: 0.06; filter: blur(1px);
    pointer-events: none; user-select: none;
}
.logros-hero-content {
    position: relative; z-index: 1;
    padding: 24px 20px; width: 100%;
}
.logros-eyebrow {
    font-family: var(--font-display); font-size: 0.68rem; font-weight: 800;
    letter-spacing: 4px; text-transform: uppercase; color: var(--red);
    margin-bottom: 10px;
}
.logros-title {
    font-family: var(--font-display); font-size: clamp(2.2rem, 7vw, 5rem);
    font-weight: 800; letter-spacing: -1px; text-transform: uppercase;
    line-height: 0.9; color: #FFFFFF; margin-bottom: 12px;
}
.logros-title span { color: var(--red); }
.logros-subtitle {
    font-size: 0.82rem; color: #888888; margin-bottom: 20px; max-width: 500px;
    letter-spacing: 0.3px; line-height: 1.4;
}
.logros-hero-stats {
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
}
.logros-hero-stat { text-align: left; }
.logros-hero-num {
    font-family: var(--font-display); font-size: 1.8rem; font-weight: 800;
    color: #FFFFFF; line-height: 1; display: block;
}
.logros-hero-desc {
    font-size: 0.65rem; color: #666666; text-transform: uppercase;
    letter-spacing: 1.5px; display: block; margin-top: 3px;
    font-family: var(--font-display);
}
.logros-hero-divider {
    width: 1px; height: 36px;
    background: rgba(255,255,255,0.1);
}
.logros-main-grid {
    display: grid;
    grid-template-columns: 240px 1fr;
    gap: 20px;
    align-items: start;
}
@media (max-width: 860px) {
    .logros-main-grid { grid-template-columns: 1fr; }
    .logros-sidebar-inner { position: static !important; }
}
.logros-sidebar-inner {
    background: #111111; border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 16px; position: sticky; top: 80px;
}
.logros-sidebar-title {
    font-family: var(--font-display); font-size: 0.7rem; font-weight: 800;
    letter-spacing: 2.5px; text-transform: uppercase; color: #888888;
    margin-bottom: 6px; margin-top: 20px;
}
.logros-sidebar-title:first-child { margin-top: 0; }
.logros-sidebar-sub {
    font-size: 0.72rem; color: #444444; margin-bottom: 16px;
}
.logros-lideres-list { display: flex; flex-direction: column; gap: 10px; margin-bottom: 8px; }
.logros-lider-row {
    display: flex; align-items: center; gap: 8px;
}
.logros-lider-left {
    display: flex; align-items: center; gap: 6px; min-width: 80px;
}
.logros-lider-pos {
    font-family: var(--font-display); font-size: 0.75rem; font-weight: 800;
    width: 22px; flex-shrink: 0;
}
.logros-lider-nombre {
    font-family: var(--font-display); font-size: 0.82rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.3px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.logros-lider-bar-wrap {
    flex: 1; height: 5px; background: rgba(255,255,255,0.06);
    border-radius: 3px; overflow: hidden;
}
.logros-lider-bar-fill {
    height: 100%; border-radius: 3px;
    transition: width 0.8s cubic-bezier(0.22,1,0.36,1);
}
.logros-lider-right { display: flex; align-items: baseline; gap: 1px; }
.logros-lider-count {
    font-family: var(--font-display); font-size: 0.95rem; font-weight: 800; color: #FFFFFF;
}
.logros-lider-total { font-size: 0.65rem; color: #444444; }
.logros-leyenda { margin-top: 4px; display: flex; flex-direction: column; gap: 8px; }
.logros-leyenda-row { display: flex; align-items: center; gap: 10px; }
.logros-leyenda-dot {
    width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
}
.logros-leyenda-label {
    font-family: var(--font-display); font-size: 0.8rem; font-weight: 700;
    letter-spacing: 0.5px;
}
.logros-catalogo { display: flex; flex-direction: column; gap: 28px; }
.logros-nivel-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; margin-bottom: 14px;
    background: rgba(255,255,255,0.03); border-radius: 8px;
}
.logros-nivel-label {
    font-family: var(--font-display); font-size: 0.88rem; font-weight: 800;
    letter-spacing: 2px; text-transform: uppercase;
}
.logros-nivel-sub {
    font-size: 0.7rem; color: #555555; font-family: var(--font-display);
    font-weight: 600; letter-spacing: 1px;
}
.logros-cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 10px;
}
@media (max-width: 600px) {
    .logros-cards-grid { grid-template-columns: 1fr; }
}
.logro-card {
    position: relative; border-radius: 12px;
    padding: 16px 16px 14px; display: flex; align-items: flex-start; gap: 12px;
    transition: transform 0.18s, box-shadow 0.18s;
    overflow: hidden;
}
.logro-card::before {
    content: ''; position: absolute; inset: 0; opacity: 0;
    background: radial-gradient(ellipse at 0% 50%, rgba(255,255,255,0.04) 0%, transparent 60%);
    transition: opacity 0.2s;
}
.logro-desbloqueado:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.4);
}
.logro-desbloqueado:hover::before { opacity: 1; }
.logro-bloqueado { filter: saturate(0.1); }
.badge-lock {
    position: absolute; top: 10px; right: 12px;
    font-size: 0.8rem; opacity: 0.35;
}
.logro-emoji-wrap {
    width: 48px; height: 48px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.logro-emoji { font-size: 1.5rem; line-height: 1; }
.logro-content { flex: 1; min-width: 0; }
.logro-nombre {
    font-family: var(--font-display); font-size: 0.95rem; font-weight: 800;
    letter-spacing: 0.3px; text-transform: uppercase; margin-bottom: 4px;
    line-height: 1.1;
}
.logro-desc-corta {
    font-family: var(--font-display); font-size: 0.76rem; font-weight: 600;
    letter-spacing: 0.2px; margin-bottom: 5px; line-height: 1.4;
}
.logro-desc-larga {
    font-size: 0.72rem; line-height: 1.55; margin-bottom: 10px;
}
.badge-ganadores { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 4px; }
.badge-ganador-chip {
    font-family: var(--font-display); font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.5px; text-transform: uppercase;
    background: rgba(255,255,255,0.08); color: #CCCCCC;
    padding: 3px 9px; border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.1);
}
.badge-nadie {
    font-size: 0.68rem; color: #333333; font-style: italic;
    font-family: var(--font-display);
}
/* ═══════════════════════════════════════════════════════ */
"""

LOGROS_JS = """
// Animar barras de progreso al activar la pestaña de logros
(function() {
    var originalOpenTab = window.openTab;
    window.openTab = function(evt, panelId) {
        originalOpenTab(evt, panelId);
        if (panelId === 'panel-logros') {
            document.querySelectorAll('.logros-lider-bar-fill').forEach(function(el) {
                var w = el.style.width;
                el.style.width = '0';
                setTimeout(function() { el.style.width = w; }, 80);
            });
        }
    };
})();
"""

CAL_CSS = """
/* ═══════════════════ CALENDARIO VISUAL ═══════════════════ */
.cal-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 10px;
}
@media (max-width: 480px) {
    .cal-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
}
.cal-card {
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--bg-2);
    padding: 12px 12px 10px;
    position: relative;
    overflow: hidden;
    transition: transform 0.15s, opacity 0.2s;
}
.cal-card:not(.cancelled):hover { transform: translateY(-2px); }
.cal-card.past { opacity: 0.42; filter: saturate(0.25); }
.cal-card.cancelled { opacity: 0.22; filter: saturate(0); pointer-events: none; }
.cal-card.next { border-color: rgba(225,6,0,0.45); background: rgba(225,6,0,0.05); }
.cal-card.next::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--red);
}
.cal-card.future { opacity: 0.68; }
.rnd-badge {
    font-family: var(--font-display); font-size: 0.6rem; font-weight: 800;
    letter-spacing: 1.5px; color: var(--muted-2); margin-bottom: 6px; display: block;
}
.cal-flag { font-size: 1.4rem; margin-bottom: 5px; display: block; line-height: 1; }
.cal-name {
    font-family: var(--font-display); font-size: 0.9rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.3px; line-height: 1.1; margin-bottom: 5px;
}
.cal-date-row { font-size: 0.72rem; color: var(--muted); margin-bottom: 2px; }
.cal-time-arg { font-size: 0.68rem; color: var(--muted-2); margin-bottom: 8px; }
.status-pill {
    display: inline-flex; align-items: center; gap: 4px;
    font-family: var(--font-display); font-size: 0.62rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    padding: 3px 7px; border-radius: 20px;
}
.status-pill .dot { width: 5px; height: 5px; border-radius: 50%; background: currentColor; display: inline-block; }
.status-done   { background: rgba(34,197,94,0.1);   color: #22c55e; border: 1px solid rgba(34,197,94,0.2); }
.status-next   { background: rgba(225,6,0,0.12);    color: var(--red); border: 1px solid rgba(225,6,0,0.3); }
.status-future { background: rgba(255,255,255,0.05); color: var(--muted-2); border: 1px solid var(--border); }
.status-cancel { background: rgba(255,255,255,0.03); color: #333; border: 1px solid rgba(255,255,255,0.05); }
.cd-mini {
    margin-top: 10px; padding-top: 10px;
    border-top: 1px solid rgba(225,6,0,0.2);
}
.cd-mini-label {
    font-family: var(--font-display); font-size: 0.58rem; color: var(--muted);
    letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px;
}
.cd-mini-nums { display: flex; gap: 2px; align-items: baseline; flex-wrap: wrap; }
.cd-num {
    font-family: var(--font-display); font-size: 1.2rem; font-weight: 800;
    color: var(--text); line-height: 1; min-width: 24px; text-align: center;
}
.cd-unit-row { display: flex; gap: 0; margin-top: 2px; }
.cd-unit {
    font-size: 0.55rem; color: var(--muted-2); letter-spacing: 0.8px;
    text-transform: uppercase;
}
.cd-sep {
    font-family: var(--font-display); font-size: 1rem; font-weight: 800;
    color: var(--red); align-self: flex-start; margin-top: 2px; line-height: 1;
}
.cal-progress-bar {
    height: 3px; background: rgba(255,255,255,0.07); border-radius: 3px; overflow: hidden;
}
.cal-progress-fill {
    height: 100%; background: var(--red); border-radius: 3px;
    transition: width 1s cubic-bezier(0.22,1,0.36,1);
}
/* ═══════════════════════════════════════════════════════════ */
"""

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
    ax.set_facecolor('#0D0D0D'); fig.patch.set_facecolor('#0D0D0D')
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333333'); ax.spines['left'].set_visible(False)
    ax.set_axisbelow(True); ax.xaxis.grid(True, color='#1E1E1E', linewidth=0.8)
    plt.tight_layout(pad=1.5)
    buf = BytesIO(); fig.savefig(buf, format="png", bbox_inches='tight', dpi=130); buf.seek(0)
    plt.close(fig)
    return base64.b64encode(buf.read()).decode('utf-8')

# =========================
# SPARKLINE DE PERFIL
# =========================
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

# =========================
# GENERAR PERFILES POR PARTICIPANTE
# =========================
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
        <div class="perfil-card" id="perfil-{idx}">
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
        <div class="stat-card accent"><div class="stat-num">{total_participantes}</div><div class="stat-desc">Participantes</div></div>
        <div class="stat-card"><div class="stat-num">{total_predicciones}</div><div class="stat-desc">Predicciones totales</div></div>
        <div class="stat-card"><div class="stat-num">{puntos_totales}</div><div class="stat-desc">Puntos distribuidos</div></div>
        <div class="stat-card"><div class="stat-num">{promedio_puntos:.1f}</div><div class="stat-desc">Promedio por predicción</div></div>
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
    ahora = datetime.now(timezone.utc)
    for item in CALENDARIO:
        if item.get("FechaISO") is None:
            continue
        try:
            fecha = datetime.fromisoformat(item["FechaISO"])
            if fecha > ahora:
                return item["Carrera"], item["FechaISO"]
        except Exception:
            continue
    return "FIN DE TEMPORADA", ""

# =========================
# GENERAR CALENDARIO VISUAL HTML
# =========================
def generar_calendario_visual(proxima_iso: str) -> str:
    ahora_utc = datetime.now(timezone.utc)
    total_validas = sum(1 for e in CALENDARIO if e.get("FechaISO"))
    completadas = 0
    proxima_encontrada = False
    cal_cards = []

    STATUS_LABEL = {
        "past": "Completada", "next": "Próxima",
        "future": "Pendiente", "cancelled": "Cancelada"
    }
    STATUS_CLASS = {
        "past": "status-done", "next": "status-next",
        "future": "status-future", "cancelled": "status-cancel"
    }

    for entry in CALENDARIO:
        raw_nombre  = entry["Carrera"]
        raw_jornada = entry["Jornada"]
        is_cancelled = "<s>" in raw_nombre

        nombre_limpio  = re.sub(r'<[^>]+>', '', raw_nombre).strip()
        jornada_limpio = re.sub(r'<[^>]+>', '', raw_jornada).strip()
        fecha_limpio   = re.sub(r'<[^>]+>', '', entry["Fecha"]).strip()
        hora_arg_limpio = re.sub(r'<[^>]+>', '', entry["Hora Argentina"]).strip()

        nombre_key = nombre_limpio.capitalize()
        flag = FLAG_MAP.get(nombre_key, "🏁")
        if flag == "🏁":
            for k, v in FLAG_MAP.items():
                if k.lower() == nombre_limpio.lower():
                    flag = v
                    break

        iso = entry.get("FechaISO")

        if is_cancelled or iso is None:
            status = "cancelled"
        else:
            try:
                fecha_dt = datetime.fromisoformat(iso)
                if fecha_dt < ahora_utc:
                    status = "past"
                    completadas += 1
                elif not proxima_encontrada:
                    status = "next"
                    proxima_encontrada = True
                else:
                    status = "future"
            except Exception:
                status = "future"

        def td(s):
            return f"<s>{s}</s>" if is_cancelled else s

        pill = (f'<span class="status-pill {STATUS_CLASS[status]}">'
                f'<span class="dot"></span>{STATUS_LABEL[status]}</span>')

        cd_html = ""
        if status == "next":
            cd_html = (
                '<div class="cd-mini">'
                '<div class="cd-mini-label">Faltan</div>'
                '<div class="cd-mini-nums">'
                '<div class="cd-num" id="cdn-d">--</div>'
                '<span class="cd-sep">:</span>'
                '<div class="cd-num" id="cdn-h">--</div>'
                '<span class="cd-sep">:</span>'
                '<div class="cd-num" id="cdn-m">--</div>'
                '<span class="cd-sep">:</span>'
                '<div class="cd-num" id="cdn-s">--</div>'
                '</div>'
                '<div class="cd-unit-row" style="display:flex;gap:0;margin-top:3px;">'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">días</span>'
                '<span class="cd-unit" style="min-width:14px;"></span>'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">hrs</span>'
                '<span class="cd-unit" style="min-width:14px;"></span>'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">min</span>'
                '<span class="cd-unit" style="min-width:14px;"></span>'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">seg</span>'
                '</div>'
                '</div>'
            )

        card = (
            f'<div class="cal-card {status}">'
            f'<span class="rnd-badge">{td(jornada_limpio)}</span>'
            f'<span class="cal-flag">{flag}</span>'
            f'<div class="cal-name">{td(nombre_limpio)}</div>'
            f'<div class="cal-date-row">{td(fecha_limpio)}</div>'
            f'<div class="cal-time-arg">ARG {td(hora_arg_limpio)}</div>'
            f'{pill}'
            f'{cd_html}'
            f'</div>'
        )
        cal_cards.append(card)

    pct = round(completadas / total_validas * 100) if total_validas > 0 else 0
    canceladas_n = sum(1 for e in CALENDARIO if "<s>" in e["Carrera"] or e.get("FechaISO") is None)

    return f"""
<div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center;">
    <div class="section-label" style="margin:0;">Progreso de temporada:</div>
    <div style="flex:1;min-width:120px;max-width:340px;">
        <div class="cal-progress-bar">
            <div class="cal-progress-fill" style="width:{pct}%;"></div>
        </div>
    </div>
    <div style="font-size:.78rem;color:var(--muted);font-weight:600;">
        {completadas}/{total_validas} carreras · {canceladas_n} canceladas
    </div>
</div>
<div class="cal-grid">
{''.join(cal_cards)}
</div>"""


# =========================
# GENERAR HTML COMPLETO
# =========================
def generar_html(rankings_por_carrera: List[pd.DataFrame],
                 ranking_acumulado: pd.DataFrame,
                 grafico_barras: str,
                 stats_adicionales: str,
                 perfiles_html: str,
                 badges_por_participante: Dict[str, List[Dict]]) -> str:

    proxima_carrera, proxima_iso = obtener_proxima_carrera()

    # ---- Ranking acumulado ----
    if not ranking_acumulado.empty:
        rows_html = ""
        for _, row in ranking_acumulado.iterrows():
            pos = row['Posición']; email = row['Dirección de correo electrónico']
            nombre = email.split('@')[0]; pts = row['Puntos']
            cambio = row.get('Cambio', '—')
            if pos == 1:   medal = '<span class="medal gold">1</span>';   rc = "row-first"
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
        <p class="section-label" style="margin-bottom:8px;color:var(--muted);">Tocá una fila para ver el perfil</p>
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
    fecha_actual     = datetime.now().strftime("%d/%m/%Y · %H:%M")

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
    --red: #E10600; --bg: #080808; --bg-2: #111111; --bg-3: #181818; --bg-4: #1F1F1F;
    --border: rgba(255,255,255,0.07); --border-bright: rgba(255,255,255,0.13);
    --text: #F0F0F0; --muted: #888888; --muted-2: #555555;
    --gold: #FFD700; --silver: #C0C0C0; --bronze: #CD7F32;
    --green: #22c55e; --danger: #ef4444;
    --font-display: 'Barlow Condensed', sans-serif;
    --font-body: 'Barlow', sans-serif;
}}
html {{ scroll-behavior: smooth; }}
body {{ font-family: var(--font-body); background: var(--bg); color: var(--text);
        min-height: 100vh; font-size: 15px; line-height: 1.55; -webkit-font-smoothing: antialiased; }}

/* ═══ HEADER ═══ */
.site-header {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(8,8,8,0.96); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
}}
.header-inner {{
    max-width: 1200px; margin: 0 auto; padding: 0 16px;
    display: flex; align-items: center; justify-content: space-between;
    min-height: 56px; gap: 12px; flex-wrap: wrap; row-gap: 6px;
}}
/* En pantallas muy angostas el countdown pasa a su propia fila para no cortarse */
@media (max-width: 480px) {{
    .header-inner {{ padding: 8px 16px; }}
    .countdown-wrap {{ width: 100%; justify-content: flex-end; }}
}}
.header-brand {{ display: flex; align-items: center; gap: 10px; flex-shrink: 0; }}
.brand-stripe {{ width: 3px; height: 28px; background: var(--red); border-radius: 2px; }}
.brand-text {{ font-family: var(--font-display); font-size: 1.1rem; font-weight: 800;
               letter-spacing: 0.5px; text-transform: uppercase; line-height: 1.1; }}
.brand-sub {{ font-size: 0.62rem; color: var(--muted); font-weight: 400;
              letter-spacing: 2px; text-transform: uppercase; margin-top: 1px; display: block; }}

/* Countdown en header — colapsa en pantallas muy chicas */
.countdown-wrap {{ display: flex; align-items: center; gap: 8px; }}
.countdown-label {{
    font-family: var(--font-display); font-size: 0.6rem; font-weight: 700;
    letter-spacing: 2px; color: var(--muted); text-transform: uppercase;
    white-space: nowrap; display: none;
}}
@media (min-width: 480px) {{ .countdown-label {{ display: block; }} }}
.countdown-race {{
    font-family: var(--font-display); font-size: 0.78rem; font-weight: 800;
    color: var(--red); text-transform: uppercase; letter-spacing: 0.5px;
    white-space: nowrap; display: none;
    max-width: 38vw; overflow: hidden; text-overflow: ellipsis;
}}
@media (min-width: 380px) {{ .countdown-race {{ display: block; }} }}
.countdown-timer {{ display: flex; gap: 4px; flex-shrink: 0; }}
.countdown-unit {{ text-align: center; }}
.countdown-num {{
    font-family: var(--font-display); font-size: 1.25rem; font-weight: 800;
    color: var(--text); line-height: 1; display: block; min-width: 28px;
}}
.countdown-unit-label {{
    font-size: 0.52rem; color: var(--muted); letter-spacing: 0.8px;
    text-transform: uppercase; display: block;
}}
.countdown-sep {{
    font-family: var(--font-display); font-size: 1.1rem; font-weight: 700;
    color: var(--red); align-self: flex-start; margin-top: 2px; line-height: 1;
}}
/* Ocultar días en mobile para ahorrar espacio si es necesario */
.cd-days-unit {{ display: none; }}
.cd-days-sep  {{ display: none; }}
@media (min-width: 420px) {{
    .cd-days-unit {{ display: block; }}
    .cd-days-sep  {{ display: block; }}
}}
/* Ocultar segundos en pantallas muy chicas: ahorra ancho y evita que el header se corte */
@media (max-width: 480px) {{
    .cd-sec-unit {{ display: none; }}
    .cd-sec-sep  {{ display: none; }}
}}

/* ═══ NAV TABS ═══ */
.tab-nav {{
    background: var(--bg-2); border-bottom: 1px solid var(--border);
    overflow-x: auto; scrollbar-width: none; -webkit-overflow-scrolling: touch;
}}
.tab-nav::-webkit-scrollbar {{ display: none; }}
.tab-nav-inner {{
    max-width: 1200px; margin: 0 auto;
    padding: 0 12px; display: flex;
    /* No forzar min-width — que scrollee naturalmente */
}}
.tab-btn {{
    font-family: var(--font-display); font-size: 0.8rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase; color: var(--muted);
    background: none; border: none; border-bottom: 3px solid transparent;
    padding: 12px 14px; cursor: pointer; white-space: nowrap; flex-shrink: 0;
    transition: color 0.2s, border-color 0.2s;
    /* Tap target mínimo */
    min-height: 44px; display: inline-flex; align-items: center;
}}
.tab-btn:hover {{ color: var(--text); }}
.tab-btn.active {{ color: var(--text); border-bottom-color: var(--red); }}

/* ═══ MAIN ═══ */
.main {{ max-width: 1200px; margin: 0 auto; padding: 24px 14px 80px; }}
.tab-panel {{ display: none; }}
.tab-panel.active {{ display: block; animation: fadeIn 0.25s ease; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; }} }}
.section-heading {{
    font-family: var(--font-display); font-size: clamp(1.6rem, 5vw, 2rem);
    font-weight: 800; letter-spacing: -0.5px; text-transform: uppercase;
    margin-bottom: 8px; line-height: 1;
}}
.section-heading span {{ color: var(--red); }}
.section-label {{
    font-family: var(--font-display); font-size: 0.7rem; font-weight: 700;
    letter-spacing: 2.5px; text-transform: uppercase; color: var(--muted);
    margin-bottom: 12px; margin-top: 4px;
}}

/* ═══ TABLA ═══ */
.table-wrapper {{
    overflow-x: auto; border-radius: 12px; border: 1px solid var(--border);
    background: var(--bg-2); -webkit-overflow-scrolling: touch;
    /* Asegurar que el scroll sea suave */
    scroll-snap-type: x proximity;
}}
.data-table {{
    width: 100%; border-collapse: collapse;
    /* min-width adaptable: no forzar ancho que rompe mobile */
}}
.data-table th {{
    font-family: var(--font-display); font-size: 0.7rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase; color: var(--muted);
    padding: 12px 14px; border-bottom: 1px solid var(--border);
    text-align: left; background: var(--bg-3); white-space: nowrap;
}}
.data-table td {{ padding: 12px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
@media (max-width: 400px) {{
    .data-table th {{ padding: 10px 8px; font-size: 0.62rem; letter-spacing: 1px; }}
    .data-table td {{ padding: 10px 8px; }}
    .leaderboard .medal {{ width: 24px; height: 24px; font-size: 0.75rem; }}
    .leaderboard .pts-big {{ font-size: 1.1rem; }}
}}
.data-table tr:last-child td {{ border-bottom: none; }}
.data-table tr:hover td {{ background: rgba(255,255,255,0.025); }}
.data-table .row-first td {{ background: rgba(225,6,0,0.05); }}
.medal {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%;
    font-family: var(--font-display); font-weight: 800; font-size: 0.85rem;
}}
.medal.gold   {{ background: rgba(255,215,0,0.15);   color: var(--gold);   border: 1px solid rgba(255,215,0,0.3); }}
.medal.silver {{ background: rgba(192,192,192,0.12); color: var(--silver); border: 1px solid rgba(192,192,192,0.25); }}
.medal.bronze {{ background: rgba(205,127,50,0.12);  color: var(--bronze); border: 1px solid rgba(205,127,50,0.25); }}
.medal.plain  {{ background: var(--bg-4); color: var(--muted); border: 1px solid var(--border); }}
.driver-name  {{ display: block; font-weight: 600; font-size: 0.9rem; }}
.driver-email {{ display: block; font-size: 0.72rem; color: var(--muted); margin-top: 1px; }}
@media (max-width: 480px) {{
    .driver-email {{ display: none; }}
}}
.pts-big  {{ font-family: var(--font-display); font-size: 1.25rem; font-weight: 800; }}
.pts-chip {{
    font-family: var(--font-display); font-size: 0.95rem; font-weight: 700;
    background: var(--bg-4); padding: 3px 9px; border-radius: 6px; border: 1px solid var(--border);
}}
.pts-tag {{ font-size: 0.7rem; color: var(--muted); font-weight: 400; }}
.trend-up      {{ color: var(--green);   font-weight: 700; font-size: 0.85rem; }}
.trend-down    {{ color: var(--danger);  font-weight: 700; font-size: 0.85rem; }}
.trend-neutral {{ color: var(--muted-2); font-weight: 700; }}
.divider {{ height: 1px; background: var(--border); margin: 24px 0; }}

/* ═══ CHARTS ═══ */
.chart-block {{
    background: var(--bg-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px; margin-bottom: 20px;
}}
.chart-title {{
    font-family: var(--font-display); font-size: 0.7rem; font-weight: 700;
    letter-spacing: 2px; text-transform: uppercase; color: var(--muted); margin-bottom: 14px;
}}
.chart-img {{ width: 100%; height: auto; display: block; border-radius: 8px; }}

/* ═══ EXPORT ═══ */
.export-bar {{ display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }}
.export-btn {{
    font-family: var(--font-display); font-size: 0.75rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase; background: var(--bg-3);
    border: 1px solid var(--border-bright); color: var(--text);
    padding: 9px 16px; border-radius: 8px; cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
    min-height: 42px; display: inline-flex; align-items: center;
}}
.export-btn:hover {{ background: var(--bg-4); border-color: var(--red); color: var(--red); }}
.export-btn.primary {{ background: var(--red); border-color: var(--red); color: #fff; }}
.export-btn.primary:hover {{ background: #c50500; }}
.export-btn-sm {{ font-size: 0.72rem; padding: 7px 13px; letter-spacing: 0.8px; }}
.export-btn:disabled {{ opacity: 0.6; cursor: wait; }}

/* ═══ RACE ACCORDION ═══ */
.race-block {{
    border: 1px solid var(--border); border-radius: 12px; overflow: hidden;
    margin-bottom: 10px; background: var(--bg-2);
}}
.race-header {{
    width: 100%; background: var(--bg-3); border: none; color: var(--text);
    padding: 14px 16px; display: flex; align-items: center; justify-content: space-between;
    cursor: pointer; transition: background 0.15s; gap: 10px;
    min-height: 52px;
}}
.race-header:hover {{ background: var(--bg-4); }}
.race-title-wrap {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
.race-badge {{
    font-family: var(--font-display); font-size: 0.7rem; font-weight: 800;
    letter-spacing: 1.5px; background: var(--red); color: #fff;
    padding: 3px 7px; border-radius: 5px; flex-shrink: 0;
}}
.race-title {{
    font-family: var(--font-display); font-size: 1rem; font-weight: 700;
    letter-spacing: 0.3px; text-transform: uppercase;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.toggle-icon {{
    font-size: 1.2rem; color: var(--muted); font-style: normal;
    transition: transform 0.2s; flex-shrink: 0; line-height: 1;
}}
.race-body {{ display: none; padding: 16px; border-top: 1px solid var(--border); }}
.detail-row {{
    border: 1px solid var(--border); border-radius: 8px; overflow: hidden; margin-bottom: 8px;
}}
.detail-toggle {{
    width: 100%; background: var(--bg-4); border: none; color: var(--text);
    padding: 12px 14px; display: flex; align-items: center; justify-content: space-between;
    cursor: pointer; font-size: 0.88rem; font-weight: 600; transition: background 0.15s; gap: 8px;
    min-height: 48px;
}}
.detail-toggle:hover {{ background: #262626; }}
.detail-body {{
    display: none; padding: 12px 14px; background: var(--bg-2);
    border-top: 1px solid var(--border);
}}
.detail-text {{ font-size: 0.84rem; color: #CCCCCC; line-height: 1.7; }}

/* ═══ STATS ═══ */
.stats-grid {{
    display: grid; grid-template-columns: repeat(2, 1fr);
    gap: 10px; margin-bottom: 20px;
}}
@media (min-width: 600px) {{
    .stats-grid {{ grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
}}
.stat-card {{
    background: var(--bg-2); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px 14px; text-align: center;
}}
.stat-card.accent {{ border-color: var(--red); background: rgba(225,6,0,0.06); }}
.stat-num  {{
    font-family: var(--font-display); font-size: 2.2rem; font-weight: 800;
    color: var(--text); line-height: 1; margin-bottom: 5px;
}}
.stat-desc {{
    font-size: 0.72rem; color: var(--muted); text-transform: uppercase;
    letter-spacing: 1px; font-family: var(--font-display);
}}
.leader-banner {{
    background: rgba(225,6,0,0.08); border: 1px solid rgba(225,6,0,0.25);
    border-radius: 12px; padding: 16px 18px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
}}
.leader-label {{
    font-family: var(--font-display); font-size: 0.65rem; letter-spacing: 3px;
    font-weight: 800; color: var(--red); text-transform: uppercase; flex-shrink: 0;
}}
.leader-name  {{
    font-family: var(--font-display); font-size: 1.3rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.5px;
}}
.leader-email {{ font-size: 0.78rem; color: var(--muted); margin-left: auto; }}
@media (max-width: 480px) {{ .leader-email {{ display: none; }} }}

.cal-carrera {{ font-family: var(--font-display); font-weight: 700; font-size: 0.9rem; letter-spacing: 0.3px; }}

/* ═══ PERFILES ═══ */
.perfiles-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 14px;
}}
@media (max-width: 480px) {{
    .perfiles-grid {{ grid-template-columns: 1fr; gap: 12px; }}
}}
.perfil-card {{
    background: var(--bg-2); border: 1px solid var(--border);
    border-radius: 14px; overflow: hidden;
}}
.perfil-header {{
    display: flex; align-items: center; gap: 12px; padding: 14px 16px;
    background: var(--bg-3); border-bottom: 1px solid var(--border);
}}
.perfil-avatar {{
    width: 44px; height: 44px; border-radius: 50%; display: flex;
    align-items: center; justify-content: center; font-family: var(--font-display);
    font-weight: 800; font-size: 1rem; flex-shrink: 0;
}}
.perfil-info {{ flex: 1; min-width: 0; }}
.perfil-nombre {{
    font-family: var(--font-display); font-size: 1rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.5px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.perfil-email {{
    font-size: 0.7rem; color: var(--muted); white-space: nowrap;
    overflow: hidden; text-overflow: ellipsis;
}}
.perfil-pos-wrap {{ display: flex; flex-direction: column; align-items: center; gap: 3px; flex-shrink: 0; }}
.perfil-pts {{ font-family: var(--font-display); font-size: 1.4rem; font-weight: 800; line-height: 1; }}

/* Stats mini: 4 col en desktop, 2x2 en mobile */
.perfil-stats-mini {{
    display: grid; grid-template-columns: repeat(4, 1fr);
    border-bottom: 1px solid var(--border);
}}
@media (max-width: 400px) {{
    .perfil-stats-mini {{
        grid-template-columns: repeat(2, 1fr);
    }}
    .perfil-stat {{ border-bottom: 1px solid var(--border); }}
    .perfil-stat:nth-child(3),
    .perfil-stat:nth-child(4) {{ border-bottom: none; }}
    .perfil-stat:nth-child(2),
    .perfil-stat:nth-child(4) {{ border-right: none; }}
}}
.perfil-stat {{
    padding: 12px 8px; text-align: center;
    border-right: 1px solid var(--border);
}}
.perfil-stat:last-child {{ border-right: none; }}
.perfil-stat-num   {{
    font-family: var(--font-display); font-size: 1.3rem; font-weight: 800;
    color: var(--text); line-height: 1;
}}
.perfil-stat-label {{
    font-size: 0.62rem; color: var(--muted); text-transform: uppercase;
    letter-spacing: 0.8px; margin-top: 3px; line-height: 1.3;
}}
.perfil-spark-wrap {{ padding: 14px 14px 8px; border-bottom: 1px solid var(--border); }}
.spark-img {{ width: 100%; height: auto; display: block; border-radius: 6px; }}
.perfil-hist-toggle {{ padding: 4px 0; }}
.perfil-export-bar {{ padding: 10px 14px 12px; display: flex; justify-content: flex-end; }}

/* ═══ BADGES EN PERFIL ═══ */
.perfil-badges-wrap {{ padding: 12px 14px; border-bottom: 1px solid var(--border); }}
.badges-row {{ display: flex; flex-wrap: wrap; gap: 7px; margin-top: 8px; }}
.badge-hint {{
    font-size: 0.6rem; color: var(--muted-2); font-weight: 400;
    letter-spacing: 0; margin-left: 2px;
}}
.badge-chip {{
    position: relative;
    display: inline-flex; align-items: center; gap: 5px;
    padding: 6px 11px; border-radius: 20px;
    font-family: var(--font-display); font-size: 0.8rem; font-weight: 700; letter-spacing: 0.3px;
    cursor: pointer; border: none;
    transition: opacity 0.15s, transform 0.1s;
    user-select: none; -webkit-user-select: none;
    /* Tap target adecuado */
    min-height: 40px;
}}
.badge-chip:hover {{ opacity: 0.88; }}
@media (hover: hover) {{
    .badge-chip:hover {{ transform: translateY(-1px); }}
}}
.badge-chip:active {{ transform: scale(0.97); }}
.badge-emoji {{ font-size: 0.95rem; line-height: 1; }}
.badge-nombre {{ white-space: nowrap; }}
.badge-nivel-tag {{ font-size: 0.72rem; line-height: 1; margin-left: 1px; opacity: 0.85; }}
.badge-counter {{
    display: inline-flex; align-items: center;
    background: rgba(255,255,255,0.08); color: var(--muted);
    padding: 2px 8px; border-radius: 10px;
    font-size: 0.68rem; font-weight: 700; letter-spacing: 1px;
}}

/* Tooltip de badge — usa absolute dentro de un wrapper para evitar
   el problema de position:fixed en mobile que colapsa la ventana */
.badge-tip-overlay {{
    display: none;
    position: fixed; inset: 0; z-index: 9990;
    background: rgba(0,0,0,0.01);
    /* Solo para capturar clicks fuera */
}}
.badge-tip-overlay.show {{ display: block; }}

#global-badge-tip {{
    position: fixed;
    width: min(260px, calc(100vw - 24px));
    background: #1C1C1C;
    border: 1px solid rgba(255,255,255,0.18);
    color: #E8E8E8;
    font-family: var(--font-body);
    font-size: 0.82rem;
    font-weight: 400;
    line-height: 1.55;
    padding: 10px 14px;
    border-radius: 10px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.7);
    pointer-events: none;
    z-index: 9999;
    white-space: normal;
    opacity: 0;
    transition: opacity 0.16s;
}}
#global-badge-tip.tip-show {{ opacity: 1; }}
#global-badge-tip::after {{
    content: '';
    position: absolute;
    left: var(--al, 50%);
    transform: translateX(-50%);
    border: 7px solid transparent;
}}
#global-badge-tip[data-pos="above"]::after {{
    top: 100%;
    border-top-color: #1C1C1C;
}}
#global-badge-tip[data-pos="below"]::after {{
    bottom: 100%;
    border-bottom-color: #1C1C1C;
}}

/* ═══ EMPTY ═══ */
.empty-msg {{ color: var(--muted); font-size: 0.9rem; font-style: italic; padding: 20px 0; }}

/* ═══ FOOTER ═══ */
.site-footer {{
    border-top: 1px solid var(--border); padding: 18px;
    text-align: center; font-size: 0.75rem; color: var(--muted-2);
}}
.footer-stripe {{ width: 28px; height: 3px; background: var(--red); border-radius: 2px; margin: 0 auto 10px; }}

/* ═══ PRINT ═══ */
@media print {{
    .site-header, .tab-nav, .export-bar, .detail-toggle, .race-header {{ display: none !important; }}
    .tab-panel {{ display: block !important; page-break-after: always; }}
    body {{ background: #fff; color: #000; }}
}}

{CAL_CSS}
{LOGROS_CSS}
</style>
</head>
<body>

<header class="site-header">
<div class="header-inner">
    <div class="header-brand">
        <div class="brand-stripe"></div>
        <div>
            <div class="brand-text">F1 Predictions</div>
            <span class="brand-sub">Torneo · 2026</span>
        </div>
    </div>
    <div class="countdown-wrap">
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:1px;margin-right:6px;">
            <div class="countdown-label">Próxima</div>
            <div class="countdown-race" id="cd-race">{proxima_carrera}</div>
        </div>
        <div class="countdown-timer" id="cd-timer">
            <div class="countdown-unit cd-days-unit">
                <span class="countdown-num" id="cd-d">--</span>
                <span class="countdown-unit-label">días</span>
            </div>
            <span class="countdown-sep cd-days-sep">:</span>
            <div class="countdown-unit">
                <span class="countdown-num" id="cd-h">--</span>
                <span class="countdown-unit-label">hrs</span>
            </div>
            <span class="countdown-sep">:</span>
            <div class="countdown-unit">
                <span class="countdown-num" id="cd-m">--</span>
                <span class="countdown-unit-label">min</span>
            </div>
            <span class="countdown-sep cd-sec-sep">:</span>
            <div class="countdown-unit cd-sec-unit">
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
    <button class="tab-btn" onclick="openTab(event,'panel-carreras')">Carreras</button>
    <button class="tab-btn" onclick="openTab(event,'panel-perfiles')">Perfiles</button>
    <button class="tab-btn" onclick="openTab(event,'panel-logros')">Logros</button>
    <button class="tab-btn" onclick="openTab(event,'panel-stats')">Stats</button>
    <button class="tab-btn" onclick="openTab(event,'panel-calendario')">Calendario</button>
</div>
</nav>

<main class="main" id="main-content">

<div id="panel-acumulado" class="tab-panel active">
    <h2 class="section-heading">Ranking <span>General</span></h2>
    <p class="section-label" style="margin-bottom:14px;">Puntos acumulados · Todas las carreras</p>
    <div class="export-bar">
        <button class="export-btn primary" onclick="exportarImagen()">⬇ Imagen</button>
        <button class="export-btn" onclick="exportarCSV()">⬇ CSV</button>
        <button class="export-btn" onclick="window.print()">🖨 Imprimir</button>
    </div>
    <div id="ranking-export-target">{ranking_acumulado_html}</div>
    <div class="divider"></div>
    <div class="chart-block">
        <div class="chart-title">Distribución de puntos</div>
        {graf_barras_html}
    </div>
</div>

<div id="panel-carreras" class="tab-panel">
    <h2 class="section-heading">Rankings <span>por Carrera</span></h2>
    <p class="section-label" style="margin-bottom:18px;">Seleccioná una carrera para ver el detalle</p>
    {rankings_por_carrera_html}
</div>

<div id="panel-perfiles" class="tab-panel">
    <h2 class="section-heading">Per<span>files</span></h2>
    <p class="section-label" style="margin-bottom:18px;">Estadísticas individuales</p>
    <div class="perfiles-grid">{perfiles_html}</div>
</div>

{logros_panel_html}

<div id="panel-stats" class="tab-panel">
    <h2 class="section-heading">Esta<span>dísticas</span></h2>
    <p class="section-label" style="margin-bottom:18px;">Resumen general de la temporada</p>
    {stats_adicionales}
</div>

<div id="panel-calendario" class="tab-panel">
    <h2 class="section-heading">Calen<span>dario</span></h2>
    <p class="section-label" style="margin-bottom:18px;">F1 2026 · Horarios ARG (GMT−3)</p>
    {calendario_html}
</div>

</main>

<footer class="site-footer">
    <div class="footer-stripe"></div>
    Generado automáticamente · {fecha_actual}
</footer>

<!-- Overlay para cerrar tooltip de badge al tocar fuera -->
<div class="badge-tip-overlay" id="badge-overlay" onclick="closeBadgeTip()"></div>

<script>
// ===== COUNTDOWN GLOBAL =====
(function() {{
    var iso = "{proxima_iso}";
    if (!iso) {{
        var t = document.getElementById('cd-timer');
        if (t) t.style.display = 'none';
        return;
    }}
    var target = new Date(iso);
    var pad = function(n) {{ return String(n).padStart(2, '0'); }};

    function tick() {{
        var diff = target - new Date();
        var vals;
        if (diff <= 0) {{
            vals = [0, 0, 0, 0];
        }} else {{
            vals = [
                Math.floor(diff / 86400000),
                Math.floor((diff % 86400000) / 3600000),
                Math.floor((diff % 3600000) / 60000),
                Math.floor((diff % 60000) / 1000)
            ];
        }}
        var ids = ['cd-d', 'cd-h', 'cd-m', 'cd-s'];
        ids.forEach(function(id, i) {{
            var el = document.getElementById(id);
            if (el) el.textContent = pad(vals[i]);
        }});
        var calIds = ['cdn-d', 'cdn-h', 'cdn-m', 'cdn-s'];
        calIds.forEach(function(id, i) {{
            var el = document.getElementById(id);
            if (el) el.textContent = pad(vals[i]);
        }});
    }}

    tick();
    setInterval(tick, 1000);
}})();

// ===== TABS =====
function openTab(evt, panelId) {{
    document.querySelectorAll('.tab-panel').forEach(function(p) {{ p.classList.remove('active'); }});
    document.querySelectorAll('.tab-btn').forEach(function(b) {{ b.classList.remove('active'); }});
    document.getElementById(panelId).classList.add('active');
    evt.currentTarget.classList.add('active');
    // Scroll tab button into view en mobile
    try {{ evt.currentTarget.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }}); }} catch(e) {{}}
}}

// ===== ACCORDION =====
function toggleDetail(id) {{
    var el = document.getElementById(id);
    var icon = document.getElementById('icon-' + id);
    var open = el.style.display === 'block';
    el.style.display = open ? 'none' : 'block';
    if (icon) icon.textContent = open ? '＋' : '－';
}}

// ===== IR A PERFIL =====
function irPerfil(idx) {{
    var btn = document.querySelector('.tab-btn[onclick*="panel-perfiles"]');
    if (btn) btn.click();
    setTimeout(function() {{
        var card = document.getElementById('perfil-' + idx);
        if (card) card.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
    }}, 180);
}}

// ===== BADGE TOOLTIP =====
// Detectar si es touch device
var isTouchDevice = (function() {{
    return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
}})();

var _gTip = null;
function _getTip() {{
    if (_gTip) return _gTip;
    _gTip = document.createElement('div');
    _gTip.id = 'global-badge-tip';
    document.body.appendChild(_gTip);
    return _gTip;
}}

function positionTip(chip) {{
    var tip = _getTip();
    var W = Math.min(260, window.innerWidth - 24);
    var GAP = 10, MARGIN = 12;
    var vw = window.innerWidth, vh = window.innerHeight;
    var r = chip.getBoundingClientRect();

    tip.style.width = W + 'px';
    tip.style.left = '-9999px';
    tip.style.top  = '-9999px';
    tip.style.display = 'block';
    var tipH = tip.offsetHeight;

    var idealLeft = r.left + r.width / 2 - W / 2;
    var clampedLeft = Math.max(MARGIN, Math.min(idealLeft, vw - W - MARGIN));
    var spaceAbove = r.top;
    var spaceBelow = vh - r.bottom;
    var pos, top;

    if (spaceAbove >= tipH + GAP && spaceAbove >= spaceBelow) {{
        pos = 'above'; top = r.top - tipH - GAP;
    }} else {{
        pos = 'below'; top = r.bottom + GAP;
        // Si no cabe abajo, centrarlo verticalmente en pantalla
        if (top + tipH > vh - MARGIN) {{
            top = Math.max(MARGIN, (vh - tipH) / 2);
        }}
    }}

    var arrowLeft = (r.left + r.width / 2) - clampedLeft;
    arrowLeft = Math.max(14, Math.min(arrowLeft, W - 14));
    tip.setAttribute('data-pos', pos);
    tip.style.setProperty('--al', arrowLeft + 'px');
    tip.style.left = clampedLeft + 'px';
    tip.style.top  = top + 'px';
}}

function showBadge(chip) {{
    if (isTouchDevice) return; // En touch solo funciona via toggleBadge
    var desc = chip.getAttribute('data-desc');
    if (!desc) return;
    var tip = _getTip();
    tip.textContent = desc;
    tip.className = '';
    positionTip(chip);
    tip.className = 'tip-show';
}}

function hideBadge(chip) {{
    if (isTouchDevice) return;
    var tip = document.getElementById('global-badge-tip');
    if (tip) tip.className = '';
}}

function closeBadgeTip() {{
    var tip = document.getElementById('global-badge-tip');
    if (tip) tip.className = '';
    var overlay = document.getElementById('badge-overlay');
    if (overlay) overlay.classList.remove('show');
    document.querySelectorAll('.badge-chip.open').forEach(function(c) {{ c.classList.remove('open'); }});
}}

function toggleBadge(chip) {{
    var wasOpen = chip.classList.contains('open');
    closeBadgeTip();
    if (!wasOpen) {{
        var desc = chip.getAttribute('data-desc');
        if (!desc) return;
        var tip = _getTip();
        tip.textContent = desc;
        tip.className = '';
        positionTip(chip);
        tip.className = 'tip-show';
        chip.classList.add('open');
        // En touch, mostrar overlay para cerrar al tocar fuera
        if (isTouchDevice) {{
            var overlay = document.getElementById('badge-overlay');
            if (overlay) overlay.classList.add('show');
        }}
    }}
}}

document.addEventListener('DOMContentLoaded', function() {{
    // Cerrar tip al hacer scroll
    window.addEventListener('scroll', function() {{
        closeBadgeTip();
    }}, {{ passive: true }});

    // Cerrar al tocar fuera (no-touch también)
    document.addEventListener('click', function(e) {{
        if (!e.target.closest('.badge-chip')) {{
            closeBadgeTip();
        }}
    }});
}});

// ===== CARGAR html2canvas =====
function cargarHtml2Canvas(cb) {{
    if (window.html2canvas) {{ cb(); return; }}
    var s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
    s.onload = cb;
    s.onerror = function() {{ alert('No se pudo cargar html2canvas. Verificá tu conexión.'); }};
    document.head.appendChild(s);
}}

// ===== EXPORTAR TARJETA DE PERFIL =====
function exportarPerfil(btnEl, idx, nombre) {{
    var originalText = btnEl.textContent;
    btnEl.textContent = '⏳ Generando...';
    btnEl.disabled = true;
    cargarHtml2Canvas(function() {{
        var card = document.getElementById('perfil-' + idx);
        card.querySelectorAll('.badge-chip.open').forEach(function(c) {{ c.classList.remove('open'); }});
        html2canvas(card, {{
            backgroundColor: '#111111',
            scale: 2, useCORS: true, allowTaint: true, logging: false,
            ignoreElements: function(el) {{
                return el.classList.contains('perfil-export-bar') ||
                       el.classList.contains('perfil-hist-toggle');
            }}
        }}).then(function(canvas) {{
            var link = document.createElement('a');
            link.download = 'f1_perfil_' + nombre + '.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
            btnEl.textContent = originalText;
            btnEl.disabled = false;
        }}).catch(function(err) {{
            console.error('Error al exportar:', err);
            alert('Error al generar la imagen. Intentá de nuevo.');
            btnEl.textContent = originalText;
            btnEl.disabled = false;
        }});
    }});
}}

// ===== EXPORTAR RANKING IMAGEN =====
function exportarImagen() {{
    cargarHtml2Canvas(function() {{
        html2canvas(document.getElementById('ranking-export-target'), {{
            backgroundColor: '#111111', scale: 2, useCORS: true, allowTaint: true, logging: false
        }}).then(function(canvas) {{
            var link = document.createElement('a');
            link.download = 'ranking_f1_2026.png';
            link.href = canvas.toDataURL('image/png');
            link.click();
        }});
    }});
}}

// ===== EXPORTAR CSV =====
function exportarCSV() {{
    var rows = document.querySelectorAll('#ranking-export-target table tr');
    if (!rows.length) return;
    var csv = '';
    rows.forEach(function(tr) {{
        var cols = Array.from(tr.querySelectorAll('th, td')).map(function(td) {{
            return '"' + (td.innerText || td.textContent).replace(/"/g, '""').trim() + '"';
        }});
        csv += cols.join(',') + '\\n';
    }});
    var blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
    var url = URL.createObjectURL(blob);
    var link = document.createElement('a');
    link.href = url; link.download = 'ranking_f1_2026.csv'; link.click();
    URL.revokeObjectURL(url);
}}

{LOGROS_JS}
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

    orden_calendario = [
        re.sub(r'<[^>]+>', '', entry["Carrera"]).strip().capitalize()
        for entry in CALENDARIO
        if "<s>" not in entry["Carrera"]
    ]

    csv_por_carrera = {}
    for archivo in os.listdir(CARPETA_RESPUESTAS):
        if archivo.endswith(".csv"):
            nombre = archivo.replace("respuestas_", "").replace(".csv", "").capitalize()
            csv_por_carrera[nombre] = archivo

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
            .sum().sort_values("Puntos", ascending=False).reset_index(drop=True)
        )
        ranking_acumulado["Posición"] = ranking_acumulado.index + 1
        ranking_acumulado = ranking_acumulado[["Posición", "Dirección de correo electrónico", "Puntos"]]
        ranking_acumulado = calcular_cambios_posiciones(all_rankings, ranking_acumulado)
    else:
        ranking_acumulado = pd.DataFrame(columns=["Posición", "Dirección de correo electrónico", "Puntos", "Cambio"])

    badges_por_participante = calcular_badges(all_rankings, all_dfs, ranking_acumulado)

    grafico_barras    = generar_grafico_barras_acumulado(ranking_acumulado)
    stats_adicionales = generar_estadisticas_adicionales(all_dfs, ranking_acumulado)
    perfiles_html     = generar_perfiles_html(all_rankings, all_dfs, ranking_acumulado, badges_por_participante)

    html_content = generar_html(
        rankings_por_carrera, ranking_acumulado,
        grafico_barras,
        stats_adicionales, perfiles_html,
        badges_por_participante
    )

    with open("ranking_f1.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print("🏁 HTML generado: ranking_f1.html")
    print("   Abrilo en cualquier navegador o celular.")

if __name__ == "__main__":
    main()