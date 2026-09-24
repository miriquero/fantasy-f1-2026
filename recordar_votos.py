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

# Dos ventanas, y el motivo es incómodo pero medible: GitHub NO ejecuta los
# cron programados como uno espera. Con `cron: 0 * * * *` (24 por día) se
# midieron 5,6 corridas diarias, el 23%, con huecos de 4,1 h de mediana y
# hasta 10,6 h. Con una ventana de 110 minutos, el recordatorio de Madrid
# nunca salió: entre las 03:28 y las 14:05 de ese día no corrió nada, y la
# carrera era 13:00. Lauta y Sergio no votaron.
#
#   ANCHA  -> asegura la entrega. Con huecos de 10,6 h como máximo, una
#             ventana de 20 h prácticamente siempre atrapa alguna corrida.
#   ULTIMA -> es un extra. Solo sale si además cae una corrida cerca de la
#             largada, y entonces avisa con urgencia.
VENTANA_ANCHA = 20 * 60
VENTANA_ULTIMA = 2 * 60


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


def cuanto_falta(minutos: float) -> str:
    """'47 minutos', '3 horas', '1 día' — como lo diría una persona."""
    minutos = round(minutos)
    if minutos < 90:
        return f"{minutos} minuto{'s' if minutos != 1 else ''}"
    horas = round(minutos / 60)
    if horas < 24:
        return f"{horas} hora{'s' if horas != 1 else ''}"
    dias = round(horas / 24)
    return f"{dias} día{'s' if dias != 1 else ''}"


def main():
    carrera, largada = proxima_carrera()
    if not carrera:
        print("No quedan carreras en el calendario.")
        return

    faltan_min = (largada - datetime.now(timezone.utc)).total_seconds() / 60
    print(f"Próxima carrera: {carrera} — larga en {faltan_min:.0f} min")

    # Avisar de una votacion ya cerrada solo genera reclamos.
    if faltan_min <= 0:
        print("La carrera ya largó. La votación está cerrada, no se avisa.")
        return

    if faltan_min > VENTANA_ANCHA:
        print(f"Todavía falta mucho (más de {VENTANA_ANCHA} min). No se avisa.")
        return

    # Dos avisos con memoria separada. El ancho es el que asegura la entrega;
    # el urgente es un extra que sale solo si alguna corrida cae cerca.
    urgente = faltan_min <= VENTANA_ULTIMA
    clave = "ultima_hora" if urgente else "recordatorios"

    estado = leer_estado()
    if ya_avisado(estado, clave, carrera):
        print(f"Ya se mandó el aviso '{clave}' de esta carrera.")
        return

    faltantes = sorted(plantel() - ya_votaron(carrera))
    if not faltantes:
        print("Votaron todos. No hace falta recordar nada.")
        return

    local = largada.astimezone()
    lista = "\n".join(f"• {n}" for n in faltantes)
    texto = (f"{carrera} larga en {cuanto_falta(faltan_min)} y todavía "
             f"no votaron:\n{lista}\n\n"
             f"La votación cierra a las {local:%H:%M}.")

    anotar("ultima_hora" if urgente else "recordatorio", texto)
    marcar_avisado(estado, clave, carrera)
    if urgente:
        # Se llegó directo a la última hora sin que saliera el aviso ancho:
        # mandarlo después ya no tendría sentido.
        marcar_avisado(estado, "recordatorios", carrera)
    guardar_estado(estado)

    print(f"Aviso '{clave}' para {len(faltantes)}: {', '.join(faltantes)}")


if __name__ == "__main__":
    configurar_salida_utf8()
    main()
