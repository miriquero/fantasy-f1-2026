# -*- coding: utf-8 -*-
"""Pilotos, calendario de la temporada y rutas de archivos."""

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
    {"Jornada": "R17", "Carrera": "AZERBAIYÁN",      "Fecha": "26 SEP",  "Hora Local": "15:00", "Hora Argentina": "08:00",              "FechaISO": "2026-09-26T08:00:00-03:00"},
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


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
