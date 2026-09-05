# -*- coding: utf-8 -*-
"""Traduce variantes de nombres de pilotos y carreras al nombre canonico."""

import re
import unicodedata
from typing import Dict

from .config import PILOTOS


def _quitar_acentos(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


ALIASES_PILOTOS = {
    # Bearman
    "oliver bearman": "Ollie Bearman",
    "oliver bearman": "Ollie Bearman",

    # Albon
    "alexander albon": "Alex Albon",

    # Antonelli
    "andrea kimi antonelli": "Kimi Antonelli",

    # Perez
    "sergio pérez": "Sergio Perez",

    # Hulkenberg
    "nico hülkenberg": "Nico Hulkenberg",

    # Bortoletto
    "gabriel bortoleto": "Gabriel Bortoletto",

    # Sainz
    "carlos sainz": "Carlos Sainz",

    # Agregados específicamente de tu JSON
    "oliver bearman": "Ollie Bearman",
    "andrea kimi antonelli": "Kimi Antonelli",
    "sergio pérez": "Sergio Perez",
    "alexander albon": "Alex Albon",
    "gabriel bortoleto": "Gabriel Bortoletto",
    "nico hülkenberg": "Nico Hulkenberg",
}


_PILOTOS_NORM = {_quitar_acentos(p).lower(): p for p in PILOTOS}


def normalizar_piloto(nombre: str) -> str:
    """Traduce cualquier variante conocida (con o sin tilde, nombre largo, etc.)
    al nombre canónico usado en PILOTOS. Si no reconoce el nombre, lo deja
    igual (y la validación posterior lo señalará como desconocido)."""
    if not nombre:
        return nombre
    limpio = _quitar_acentos(str(nombre).strip()).lower()
    if limpio in _PILOTOS_NORM:
        return _PILOTOS_NORM[limpio]
    if limpio in ALIASES_PILOTOS:
        return ALIASES_PILOTOS[limpio]

    # Ultimo recurso: emparejar por apellido. La API cambia la forma de
    # escribir los nombres sin avisar ("Oliver" por "Ollie", "Andrea Kimi
    # Antonelli" por "Kimi Antonelli"), y cada variante nueva obligaba a
    # agregar un alias a mano. Ningun apellido se repite entre los pilotos,
    # asi que esto es seguro; si alguna vez se repitiera, no se adivina.
    candidatos = [p for p in PILOTOS
                  if _quitar_acentos(p).lower().split()[-1] == limpio.split()[-1]]
    if len(candidatos) == 1:
        return candidatos[0]

    return str(nombre).strip()


def normalizar_resultados_api(resultados_por_carrera: Dict) -> Dict:
    """Normaliza pilotos Y claves de carrera"""
    nuevos = {}
    for carrera, datos in resultados_por_carrera.items():
        clave_norm = normalizar_nombre_carrera(carrera)
        if isinstance(datos, dict):
            if isinstance(datos.get("resultado_carrera"), list):
                datos["resultado_carrera"] = [normalizar_piloto(p) for p in datos["resultado_carrera"]]
            if isinstance(datos.get("vuelta_rapida"), str):
                datos["vuelta_rapida"] = normalizar_piloto(datos["vuelta_rapida"])
        nuevos[clave_norm] = datos
    return nuevos


def normalizar_nombre_carrera(nombre: str) -> str:
    """Normaliza TODOS los nombres de carrera del calendario"""
    if not nombre:
        return ""
    
    n = _quitar_acentos(str(nombre).strip().lower())
    n = re.sub(r'[^a-z0-9\s]', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip()

    reemplazos = {
        # Pares comunes (CSV → Nombre oficial)
        "gran bretana": "Gran Bretaña",
        "gran_bretana": "Gran Bretaña",
        "great britain": "Gran Bretaña",
        "silverstone": "Gran Bretaña",

        "japon": "Japon",
        "miami": "Miami",
        "canada": "Canada",
        "monaco": "Monaco",
        "barcelona": "Barcelona",
        "austria": "Austria",
        "hungria": "Hungría",
        "paises bajos": "Países Bajos",
        "paises_bajos": "Países Bajos",
        "italia": "Italia",
        "madrid": "Madrid",
        # Al calendario le faltaba la "a" ("AZERBAIYN"). Si el Google Form
        # manda "Azerbaiyán" bien escrito, sin estas dos entradas normalizaba
        # a "Azerbaiyan" y no matcheaba con la clave de resultados.json: la
        # carrera se salteaba en silencio y no puntuaba nadie.
        "azerbaiyan": "Azerbaiyan",
        "azerbaiyn": "Azerbaiyan",
        "singapur": "Singapur",
        "austin": "Austin",
        "mexico": "Mexico",
        "brasil": "Brasil",
        "las vegas": "Las Vegas",
        "qatar": "Qatar",
        "abu dhabi": "Abu Dhabi",
        "abudhabi": "Abu Dhabi",
    }

    for viejo, nuevo in reemplazos.items():
        if viejo in n or n in viejo:
            return nuevo

    # Si no encuentra coincidencia exacta, capitaliza normalmente
    return ' '.join(word.capitalize() for word in n.split())
