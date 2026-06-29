"""
fetch_votos.py
--------------
Lee las respuestas del Google Form desde Google Sheets y genera
un CSV por carrera en la carpeta `respuestas/`, respetando el
corte de votos (solo votos anteriores al inicio de la carrera).
Si una persona voto mas de una vez para la misma carrera, se queda
con el voto mas reciente.

Uso:
    python fetch_votos.py

Requiere:
    pip install google-auth google-auth-httplib2 google-api-python-client
"""

import os
import csv
import json
import re
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

# -- Configuracion ------------------------------------------------------------

SHEET_ID   = "1YSPJn9qpgPOECpW7OwX9_dCdeiB3XxrDpucujvVcA-8"
SHEET_NAME = "Respuestas de formulario 1"
CARPETA    = Path("respuestas")
SCOPES     = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
JSON_LOCAL = "fantasy-f1-500915-613a0c111715.json"

ARG = timezone(timedelta(hours=-3))

INICIO_CARRERA = {
    "Australia":    "2026-03-08T01:00:00",
    "China":        "2026-03-15T04:00:00",
    "Japon":        "2026-03-29T02:00:00",
    "Miami":        "2026-05-03T17:00:00",
    "Canada":       "2026-05-24T17:00:00",
    "Monaco":       "2026-06-07T10:00:00",
    "Barcelona":    "2026-06-14T10:00:00",
    "Austria":      "2026-06-28T10:00:00",
    "Gran Bretana": "2026-07-05T11:00:00",
    "Belgica":      "2026-07-19T10:00:00",
    "Hungria":      "2026-07-26T10:00:00",
    "Paises Bajos": "2026-08-23T10:00:00",
    "Italia":       "2026-09-06T10:00:00",
    "Madrid":       "2026-09-13T10:00:00",
    "Azerbaiyn":    "2026-09-26T08:00:00",
    "Singapur":     "2026-10-11T09:00:00",
    "Austin":       "2026-10-25T17:00:00",
    "Mexico":       "2026-11-01T17:00:00",
    "Brasil":       "2026-11-08T14:00:00",
    "Las Vegas":    "2026-11-21T01:00:00",
    "Qatar":        "2026-11-29T13:00:00",
    "Abu Dhabi":    "2026-12-06T10:00:00",
}

# -- Autenticacion ------------------------------------------------------------

def get_service():
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
    elif os.path.exists(JSON_LOCAL):
        with open(JSON_LOCAL, encoding="utf-8") as f:
            creds_dict = json.load(f)
    else:
        raise FileNotFoundError(
            f"No se encontro '{JSON_LOCAL}' ni la variable GOOGLE_SHEETS_CREDENTIALS."
        )
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)

# -- Utilidades ---------------------------------------------------------------

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def parsear_fecha(texto):
    for fmt in ("%d/%m/%Y %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(texto.strip(), fmt).replace(tzinfo=ARG)
        except ValueError:
            continue
    return None

def corte_carrera(nombre):
    clave = quitar_tildes(nombre.strip())
    iso = INICIO_CARRERA.get(clave) or INICIO_CARRERA.get(nombre.strip())
    if not iso:
        return None
    return datetime.fromisoformat(iso).replace(tzinfo=ARG)

def nombre_archivo(carrera):
    limpio = quitar_tildes(carrera).strip().lower()
    limpio = re.sub(r"[^\w\s-]", "", limpio)
    return limpio.replace(" ", "_")

# -- Logica principal ---------------------------------------------------------

def deduplicar(votos, col_email):
    """Queda con el voto mas reciente por persona."""
    if not col_email:
        return votos
    vistos = {}
    for voto in votos:
        email = voto.get(col_email, "").strip().lower()
        marca = parsear_fecha(voto.get("Marca temporal", ""))
        if email not in vistos:
            vistos[email] = (voto, marca)
        else:
            _, marca_anterior = vistos[email]
            if marca and marca_anterior and marca > marca_anterior:
                vistos[email] = (voto, marca)
    return [v for v, _ in vistos.values()]

def fetch_y_guardar():
    service = get_service()
    sheet   = service.spreadsheets()

    result = sheet.values().get(
        spreadsheetId=SHEET_ID,
        range=SHEET_NAME,
    ).execute()

    rows = result.get("values", [])
    if not rows:
        print("El Sheet esta vacio.")
        return

    headers = [h.strip() for h in rows[0]]
    filas   = rows[1:]
    print(f"Sheet leido: {len(filas)} respuestas, {len(headers)} columnas.")

    # Detectar columna de email
    col_email = next((h for h in headers if "correo" in h.lower()), None)

    por_carrera = {}
    omitidas = 0

    for fila in filas:
        row = dict(zip(headers, fila + [""] * (len(headers) - len(fila))))

        carrera = row.get("Carrera", "").strip()
        if not carrera:
            omitidas += 1
            continue

        marca = parsear_fecha(row.get("Marca temporal", ""))
        corte = corte_carrera(carrera)

        if marca and corte and marca >= corte:
            email = row.get(col_email, "") if col_email else ""
            print(f"  IGNORADO (tardio): {email} -> {carrera} ({row.get('Marca temporal')})")
            omitidas += 1
            continue

        por_carrera.setdefault(carrera, []).append(row)

    CARPETA.mkdir(exist_ok=True)
    duplicados_total = 0

    for carrera, votos in sorted(por_carrera.items()):
        antes = len(votos)
        votos = deduplicar(votos, col_email)
        duplicados = antes - len(votos)
        if duplicados:
            print(f"  DUPLICADOS descartados en {carrera}: {duplicados} voto(s) extra")
            duplicados_total += duplicados

        ruta = CARPETA / f"respuestas_{nombre_archivo(carrera)}.csv"
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(votos)
        print(f"  OK {carrera:20s} -> {ruta} ({len(votos)} votos)")

    total = sum(len(v) for v in por_carrera.values()) - duplicados_total
    print(f"\nListo. {total} votos en {len(por_carrera)} carreras.")
    if omitidas:
        print(f"   {omitidas} fila(s) ignoradas (tardias o sin carrera).")
    if duplicados_total:
        print(f"   {duplicados_total} voto(s) duplicado(s) descartado(s) (se quedo con el mas reciente).")

if __name__ == "__main__":
    fetch_y_guardar()