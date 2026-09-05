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

from f1.config import CALENDARIO
from f1.consola import configurar_salida_utf8
from f1.normalizacion import normalizar_nombre_carrera
from f1.participantes import COLUMNA_PARTICIPANTE, nombre_participante

# -- Configuracion ------------------------------------------------------------

SHEET_ID   = "1YSPJn9qpgPOECpW7OwX9_dCdeiB3XxrDpucujvVcA-8"
SHEET_NAME = "Respuestas de formulario 1"
CARPETA    = Path("respuestas")
SCOPES     = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
JSON_LOCAL = "fantasy-f1-500915-613a0c111715.json"

ARG = timezone(timedelta(hours=-3))

def _horarios_de_largada():
    """Horario de largada de cada carrera, tomado de f1/config.py.

    Antes esta tabla estaba escrita a mano tambien aca, y se habia
    desincronizado: Las Vegas tenia el corte de votos el 21/11 a la 01:00
    cuando la carrera larga el 22/11 a la 01:00 hora argentina. Los votos de
    todo ese sabado se rechazaban por "tardios". Ahora hay una sola fuente de
    verdad y no se puede volver a desfasar.
    """
    horarios = {}
    for entrada in CALENDARIO:
        iso = entrada.get("FechaISO")
        if not iso:
            continue                      # carrera tachada del calendario
        nombre = re.sub(r"<[^>]+>", "", entrada["Carrera"]).strip()
        horarios[normalizar_nombre_carrera(nombre)] = datetime.fromisoformat(iso)
    return horarios


INICIO_CARRERA = _horarios_de_largada()

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
    """Momento de largada, o None si el nombre no esta en el calendario.

    Usa el normalizador canonico del proyecto, asi que tolera mayusculas,
    tildes y guiones bajos ("PAISES BAJOS", "Paises_Bajos", "Países Bajos"
    son la misma carrera). Antes la busqueda era sensible a mayusculas y un
    voto escrito distinto se colaba sin control de horario.
    """
    return INICIO_CARRERA.get(normalizar_nombre_carrera(nombre))

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

def _sin_mails(headers, votos, col_email):
    """Cambia la columna de mail por el apodo publico.

    Los CSV de `respuestas/` estan versionados en un repo publico, asi que el
    mail no puede llegar al disco. Devuelve (cabeceras, filas) ya traducidas.
    """
    if not col_email:
        return headers, votos
    cabeceras = [COLUMNA_PARTICIPANTE if h == col_email else h for h in headers]
    filas = []
    for voto in votos:
        fila = {k: v for k, v in voto.items() if k != col_email}
        fila[COLUMNA_PARTICIPANTE] = nombre_participante(voto.get(col_email, ""))
        filas.append(fila)
    return cabeceras, filas


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
            quien = nombre_participante(row.get(col_email, "")) if col_email else "?"
            print(f"  IGNORADO (tardio): {quien} -> {carrera} ({row.get('Marca temporal')})")
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
        cabeceras, filas = _sin_mails(headers, votos, col_email)
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=cabeceras, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(filas)
        print(f"  OK {carrera:20s} -> {ruta} ({len(votos)} votos)")

    total = sum(len(v) for v in por_carrera.values()) - duplicados_total
    print(f"\nListo. {total} votos en {len(por_carrera)} carreras.")
    if omitidas:
        print(f"   {omitidas} fila(s) ignoradas (tardias o sin carrera).")
    if duplicados_total:
        print(f"   {duplicados_total} voto(s) duplicado(s) descartado(s) (se quedo con el mas reciente).")

if __name__ == "__main__":
    configurar_salida_utf8()
    fetch_y_guardar()