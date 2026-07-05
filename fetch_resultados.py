"""
fetch_resultados.py
-------------------
Consulta la API de Jolpica (sucesor de Ergast) y actualiza resultados.json
con los resultados de las carreras que ya se disputaron.

Carreras sin resultado: se consultan siempre.
Carreras ya cargadas: se re-chequean durante los 4 dias posteriores a la
carga inicial, por si la FIA aplica una penalidad que cambia el orden.
Pasados esos 4 dias, se consideran definitivas y no se vuelven a tocar.

Uso:
    python fetch_resultados.py

No requiere autenticacion ni API keys.
"""

import json
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

ARCHIVO_RESULTADOS = Path("resultados.json")
BASE_URL = "https://api.jolpi.ca/ergast/f1/2026"

DIAS_VENTANA_PENALIDAD = 3  # Cuantos dias re-chequea por si hay sanciones de la FIA

NOMBRE_A_ROUND = {
    "Australia":    1,
    "China":        2,
    "Japon":        3,
    "Miami":        4,
    "Canada":       5,
    "Monaco":       6,
    "Barcelona":    7,
    "Austria":      8,
    "Gran Bretana": 9,
    "Belgica":      10,
    "Hungria":      11,
    "Paises Bajos": 12,
    "Italia":       13,
    "Madrid":       14,
    "Azerbaiyn":    15,
    "Singapur":     16,
    "Austin":       17,
    "Mexico":       18,
    "Brasil":       19,
    "Las Vegas":    20,
    "Qatar":        23,
    "Abu Dhabi":    24,
}

COLAPINTO_NUMBER = "43"

def quitar_tildes(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FantasyF1/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERROR al consultar {url}: {e}")
        return None

def get_resultado_carrera(round_num):
    """Devuelve (lista_pilotos_ordenada, vuelta_rapida_nombre, pos_colapinto) o None."""
    url = f"{BASE_URL}/{round_num}/results.json?limit=25"
    data = fetch_json(url)
    if not data:
        return None

    try:
        races = data["MRData"]["RaceTable"]["Races"]
        if not races:
            return None

        results = races[0]["Results"]
        results_sorted = sorted(results, key=lambda r: int(r["position"]))

        pilotos = []
        vuelta_rapida = None
        pos_colapinto = None

        for r in results_sorted:
            nombre = f"{r['Driver']['givenName']} {r['Driver']['familyName']}"
            pilotos.append(nombre)

            if r.get("FastestLap", {}).get("rank") == "1":
                vuelta_rapida = nombre

            if r["Driver"]["permanentNumber"] == COLAPINTO_NUMBER or \
               r["Driver"]["familyName"].lower() == "colapinto":
                pos_colapinto = str(r["position"])

        return pilotos, vuelta_rapida or "", pos_colapinto or "0"

    except (KeyError, IndexError, TypeError) as e:
        print(f"  ERROR parseando resultado round {round_num}: {e}")
        return None

def dentro_de_ventana(fecha_iso, dias):
    """True si fecha_iso esta dentro de los ultimos N dias."""
    try:
        fecha = datetime.fromisoformat(fecha_iso)
        if fecha.tzinfo is None:
            fecha = fecha.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - fecha) <= timedelta(days=dias)
    except (ValueError, TypeError):
        return False

def main():
    if ARCHIVO_RESULTADOS.exists():
        with open(ARCHIVO_RESULTADOS, encoding="utf-8") as f:
            resultados = json.load(f)
        print(f"Archivo existente: {len(resultados)} carreras cargadas.")
    else:
        resultados = {}
        print("No existe resultados.json, se creara uno nuevo.")

    actualizadas = 0
    correcciones = 0
    sin_datos = 0
    ahora_iso = datetime.now(timezone.utc).isoformat()

    for carrera, round_num in NOMBRE_A_ROUND.items():
        clave_existente = None
        for k in resultados:
            if quitar_tildes(k).lower() == quitar_tildes(carrera).lower():
                clave_existente = k
                break

        ya_cargada = clave_existente and resultados[clave_existente].get("resultado_carrera")

        if ya_cargada:
            fecha_carga = resultados[clave_existente].get("_actualizado")
            if not fecha_carga or not dentro_de_ventana(fecha_carga, DIAS_VENTANA_PENALIDAD):
                # Fuera de la ventana de re-chequeo: se considera definitiva
                print(f"  OK (definitiva): {clave_existente}")
                continue
            # Dentro de la ventana: re-chequear por si hubo penalidad
            print(f"  Re-chequeando (dentro de ventana de {DIAS_VENTANA_PENALIDAD} dias): {clave_existente}...")
        else:
            print(f"  Consultando round {round_num}: {carrera}...")

        resultado = get_resultado_carrera(round_num)

        if resultado is None:
            if not ya_cargada:
                print(f"  -> Sin datos todavia (carrera pendiente o API no actualizada).")
                sin_datos += 1
            time.sleep(0.3)
            continue

        pilotos, vuelta_rapida, pos_colapinto = resultado
        clave = clave_existente or carrera

        if ya_cargada:
            orden_anterior = resultados[clave].get("resultado_carrera", [])
            if orden_anterior == pilotos:
                # Sin cambios, solo refrescar timestamp si ya estaba presente
                print(f"  -> Sin cambios.")
                time.sleep(0.3)
                continue
            else:
                print(f"  -> PENALIDAD DETECTADA! El orden cambio respecto a la carga anterior.")
                print(f"     Antes: {orden_anterior[0] if orden_anterior else '?'} primero")
                print(f"     Ahora: {pilotos[0] if pilotos else '?'} primero")
                correcciones += 1

        resultados[clave] = {
            "resultado_carrera": pilotos,
            "vuelta_rapida": vuelta_rapida,
            "colapinto": pos_colapinto,
            "_actualizado": ahora_iso,
        }

        print(f"  -> {clave}: P1={pilotos[0] if pilotos else '?'}, VR={vuelta_rapida}, Colapinto=P{pos_colapinto}")
        actualizadas += 1
        time.sleep(0.3)

    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\nListo.")
    print(f"  {actualizadas} carrera(s) actualizada(s) o cargada(s) por primera vez.")
    if correcciones:
        print(f"  {correcciones} carrera(s) CORREGIDA(S) por penalidad de la FIA.")
    print(f"  {sin_datos} carrera(s) pendiente(s) sin datos todavia.")
    print(f"  Archivo guardado: {ARCHIVO_RESULTADOS}")

    # Indicador para el workflow: hubo penalidad?
    if correcciones:
        with open("_penalidad_detectada.flag", "w") as f:
            f.write(str(correcciones))

if __name__ == "__main__":
    main()
