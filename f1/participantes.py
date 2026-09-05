# -*- coding: utf-8 -*-
"""Traduce el mail de cada participante al apodo que se publica.

El repo y la pagina son publicos. El Google Form identifica a cada persona por
su mail, asi que si ese valor viaja tal cual hasta el HTML terminan quedando
los mails de la familia expuestos en internet, listos para que los levante
cualquier bot. Este modulo es el unico lugar donde se hace la traduccion, y se
aplica apenas el dato entra al pipeline.

El mapa vive en `participantes.json`, en la raiz del proyecto, para que se
pueda cambiar un apodo sin tocar codigo.
"""

import json
import os
from pathlib import Path


ARCHIVO_PARTICIPANTES = "participantes.json"


VARIABLE_ENTORNO = "PARTICIPANTES_JSON"

# Nombre de la columna que identifica a la persona, ya con el apodo adentro.


COLUMNA_PARTICIPANTE = "Participante"

_mapa = None


def cargar_apodos() -> dict:
    """Lee el mapa de apodos una sola vez.

    Busca primero la variable de entorno PARTICIPANTES_JSON (asi viaja como
    Secret de GitHub Actions) y despues el archivo local. El archivo NO se
    versiona: sus claves son los mails de la familia y el repo es publico.

    Si no encuentra ninguno de los dos devuelve un mapa vacio, y
    nombre_participante() igual corta el dominio del mail.
    """
    global _mapa
    if _mapa is not None:
        return _mapa

    crudo = None
    desde_entorno = os.environ.get(VARIABLE_ENTORNO)
    if desde_entorno:
        crudo = json.loads(desde_entorno)
    else:
        ruta = Path(ARCHIVO_PARTICIPANTES)
        if ruta.exists():
            crudo = json.loads(ruta.read_text(encoding="utf-8"))

    _mapa = {} if crudo is None else {
        k.strip().lower(): v for k, v in crudo.items() if not k.startswith("_")
    }
    return _mapa


def nombre_participante(valor: str) -> str:
    """Apodo publico de un participante.

    Acepta tanto un mail como un apodo ya traducido, asi que se puede aplicar
    mas de una vez sin romper nada. Si el mail no figura en participantes.json
    igual se corta el dominio: preferimos mostrar "juan" antes que publicar
    "juan@gmail.com".
    """
    if not valor:
        return ""
    limpio = str(valor).strip()
    apodo = cargar_apodos().get(limpio.lower())
    if apodo:
        return apodo
    return limpio.split("@")[0] if "@" in limpio else limpio
