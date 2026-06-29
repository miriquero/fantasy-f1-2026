"""
fetch_resultados.py
-------------------
Consulta la API de Jolpica (sucesor de Ergast) y actualiza resultados.json
con los resultados de las carreras que ya se disputaron.

Solo actualiza carreras que no tienen resultado todavia.
Las carreras ya cargadas no se tocan.

Uso:
    python fetch_resultados.py

No requiere autenticacion ni API keys.
"""

import json
import time
import urllib.request
from pathlib import Path

ARCHIVO_RESULTADOS = Path("resultados.json")
BASE_URL = "https://api.jolpi.ca/ergast/f1/2026"

# Mapeo nombre de carrera en tu sistema -> circuitId o raceName en Jolpica
# Jolpica usa el nombre oficial del Gran Premio
NOMBRE_A_ROUND = {
    "Australia":    1,
    "China":        2,
    "Japon":        3,
    "Miami":        6,   # Bahrein(4) y Arabia Saudita(5) cancelados
    "Canada":       7,
    "Monaco":       8,
    "Barcelona":    9,
    "Austria":      10,
    "Gran Bretana": 11,
    "Belgica":      12,
    "Hungria":      13,
    "Paises Bajos": 14,
    "Italia":       15,
    "Madrid":       16,
    "Azerbaiyn":    17,
    "Singapur":     18,
    "Austin":       19,
    "Mexico":       20,
    "Brasil":       21,
    "Las Vegas":    22,
    "Qatar":        23,
    "Abu Dhabi":    24,
}

# Numero de piloto de Colapinto en 2026
COLAPINTO_NUMBER = "43"

import unicodedata

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
    """Devuelve (lista_pilotos_ordenada, vuelta_rapida_nombre) o None si no hay datos."""
    url = f"{BASE_URL}/{round_num}/results.json?limit=25"
    data = fetch_json(url)
    if not data:
        return None

    try:
        races = data["MRData"]["RaceTable"]["Races"]
        if not races:
            return None  # Carrera no disputada todavia

        results = races[0]["Results"]

        # Ordenar por posicion final
        results_sorted = sorted(results, key=lambda r: int(r["position"]))

        pilotos = []
        vuelta_rapida = None
        pos_colapinto = None

        for r in results_sorted:
            nombre = f"{r['Driver']['givenName']} {r['Driver']['familyName']}"
            pilotos.append(nombre)

            # Vuelta rapida
            if r.get("FastestLap", {}).get("rank") == "1":
                vuelta_rapida = nombre

            # Posicion de Colapinto
            if r["Driver"]["permanentNumber"] == COLAPINTO_NUMBER or \
               r["Driver"]["familyName"].lower() == "colapinto":
                pos_colapinto = str(r["position"])

        return pilotos, vuelta_rapida or "", pos_colapinto or "0"

    except (KeyError, IndexError, TypeError) as e:
        print(f"  ERROR parseando resultado round {round_num}: {e}")
        return None

def main():
    # Cargar resultados existentes
    if ARCHIVO_RESULTADOS.exists():
        with open(ARCHIVO_RESULTADOS, encoding="utf-8") as f:
            resultados = json.load(f)
        print(f"Archivo existente: {len(resultados)} carreras cargadas.")
    else:
        resultados = {}
        print("No existe resultados.json, se creara uno nuevo.")

    actualizadas = 0
    sin_datos = 0

    for carrera, round_num in NOMBRE_A_ROUND.items():
        # Buscar si ya tiene resultado (con o sin tildes)
        clave_existente = None
        for k in resultados:
            if quitar_tildes(k).lower() == quitar_tildes(carrera).lower():
                clave_existente = k
                break

        if clave_existente:
            datos = resultados[clave_existente]
            if datos.get("resultado_carrera"):
                print(f"  OK (ya cargada): {clave_existente}")
                continue

        # No tiene resultado todavia, consultar API
        print(f"  Consultando round {round_num}: {carrera}...")
        resultado = get_resultado_carrera(round_num)

        if resultado is None:
            print(f"  -> Sin datos todavia (carrera pendiente o API no actualizada).")
            sin_datos += 1
            time.sleep(0.3)
            continue

        pilotos, vuelta_rapida, pos_colapinto = resultado

        # Usar la clave existente si ya estaba en el JSON (para no cambiar el nombre)
        clave = clave_existente or carrera
        resultados[clave] = {
            "resultado_carrera": pilotos,
            "vuelta_rapida": vuelta_rapida,
            "colapinto": pos_colapinto,
        }

        print(f"  -> {clave}: P1={pilotos[0] if pilotos else '?'}, VR={vuelta_rapida}, Colapinto=P{pos_colapinto}")
        actualizadas += 1
        time.sleep(0.3)  # Respetar rate limit de la API

    # Guardar
    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\nListo.")
    print(f"  {actualizadas} carrera(s) actualizada(s) desde la API.")
    print(f"  {sin_datos} carrera(s) pendiente(s) sin datos todavia.")
    print(f"  Archivo guardado: {ARCHIVO_RESULTADOS}")

if __name__ == "__main__":
    main()
