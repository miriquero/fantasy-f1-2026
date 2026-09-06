# -*- coding: utf-8 -*-
"""
recordar_votos.py
-----------------
Avisa por WhatsApp quién todavía no votó, antes de que cierre.

Por qué existe: sobre 13 carreras se dejaron de emitir 29 votos de 130
posibles, el 22%. Y no está repartido parejo -- hay gente que se perdió más de
la mitad de las carreras. El sistema avisaba cuando el ranking ya estaba
actualizado, o sea cuando ya era tarde para votar; nadie avisaba antes.

Corre cada hora y decide solo si tiene algo que decir: manda un mensaje
únicamente en la última hora antes de la largada, si todavía hay gente sin
votar y no se avisó ya para esa carrera. El resto de las corridas no hacen
nada y no molestan a nadie.

Uso:
    python recordar_votos.py
"""

import re
import sys
from datetime import datetime, timezone

from f1.avisos import anotar, guardar_estado, leer_estado, marcar_avisado, ya_avisado
from f1.config import CALENDARIO
from f1.consola import configurar_salida_utf8
from f1.normalizacion import normalizar_nombre_carrera
from f1.participantes import nombre_participante

# El recordatorio sale en la última hora antes de la largada. Como el workflow
# corre cada hora y GitHub suele disparar los cron con algunos minutos de
# atraso, la ventana es de 110 minutos y no de 60 exactos: así siempre cae al
# menos una corrida adentro. Si entran dos, la segunda no manda nada porque el
# aviso queda registrado en estado_avisos.json.
VENTANA_MINUTOS = 110


def proxima_carrera(ahora=None):
    """(nombre, momento de largada) de la próxima carrera, o (None, None)."""
    ahora = ahora or datetime.now(timezone.utc)
    proximas = []
    for entrada in CALENDARIO:
        iso = entrada.get("FechaISO")
        if not iso:
            continue
        largada = datetime.fromisoformat(iso)
        if largada > ahora:
            nombre = re.sub(r"<[^>]+>", "", entrada["Carrera"]).strip()
            proximas.append((largada, nombre))
    if not proximas:
        return None, None
    largada, nombre = min(proximas)
    return nombre, largada


def plantel():
    """Quiénes juegan el torneo: todos los que votaron alguna vez.

    Se saca de los CSV ya versionados y no de participantes.json, asi que
    funciona igual sin el Secret cargado. Alguien que se sumo esta temporada
    aparece solo; alguien que nunca jugo no recibe recordatorios.
    """
    import csv
    import glob
    gente = set()
    for archivo in glob.glob("respuestas/*.csv"):
        for fila in csv.DictReader(open(archivo, encoding="utf-8")):
            quien = (fila.get("Participante") or "").strip()
            if quien:
                gente.add(quien)
    return gente


def ya_votaron(nombre_carrera):
    """Quiénes ya cargaron su predicción para esa carrera, según el Sheet."""
    import fetch_votos
    servicio = fetch_votos.get_service()
    filas = servicio.spreadsheets().values().get(
        spreadsheetId=fetch_votos.SHEET_ID,
        range=fetch_votos.SHEET_NAME,
    ).execute().get("values", [])
    if not filas:
        return set()

    cabeceras = [h.strip() for h in filas[0]]
    col_mail = next((h for h in cabeceras if "correo" in h.lower()), None)
    objetivo = normalizar_nombre_carrera(nombre_carrera)

    votaron = set()
    for fila in filas[1:]:
        registro = dict(zip(cabeceras, fila + [""] * (len(cabeceras) - len(fila))))
        if normalizar_nombre_carrera(registro.get("Carrera", "")) != objetivo:
            continue
        if col_mail:
            votaron.add(nombre_participante(registro.get(col_mail, "")))
    return votaron


def main():
    carrera, largada = proxima_carrera()
    if not carrera:
        print("No quedan carreras en el calendario.")
        return

    faltan_min = (largada - datetime.now(timezone.utc)).total_seconds() / 60
    print(f"Próxima carrera: {carrera} — larga en {faltan_min:.0f} min")

    if faltan_min > VENTANA_MINUTOS:
        print(f"Todavía falta mucho (más de {VENTANA_MINUTOS} min). No se avisa.")
        return

    estado = leer_estado()
    if ya_avisado(estado, "recordatorios", carrera):
        print("Ya se mandó el recordatorio de esta carrera.")
        return

    faltantes = sorted(plantel() - ya_votaron(carrera))
    if not faltantes:
        print("Votaron todos. No hace falta recordar nada.")
        return

    local = largada.astimezone()
    lista = "\n".join(f"• {n}" for n in faltantes)
    anotar("recordatorio",
           f"{carrera} larga en {round(faltan_min)} minutos y todavía "
           f"no votaron:\n{lista}\n\n"
           f"La votación cierra a las {local:%H:%M}.")

    marcar_avisado(estado, "recordatorios", carrera)
    guardar_estado(estado)
    print(f"Recordatorio para {len(faltantes)}: {', '.join(faltantes)}")


if __name__ == "__main__":
    configurar_salida_utf8()
    main()
