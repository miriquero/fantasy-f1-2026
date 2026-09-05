"""
fetch_resultados.py
-------------------
Consulta la API Jolpica y guarda solo lo necesario:
- Top 11 de la carrera
- Vuelta rápida
- Posición de Colapinto
"""

import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from f1.normalizacion import normalizar_nombre_carrera

ARCHIVO_RESULTADOS = Path("resultados.json")
BASE_URL = "https://api.jolpi.ca/ergast/f1/2026"

DIAS_VENTANA_PENALIDAD = 3

NOMBRE_A_ROUND = {
    "Australia": 1, "China": 2, "Japon": 3, "Miami": 4, "Canada": 5,
    "Monaco": 6, "Barcelona": 7, "Austria": 8, "Gran Bretana": 9,
    "Belgica": 10, "Hungría": 11, "Paises Bajos": 12, "Italia": 13,
    "Madrid": 14, "Azerbaiyn": 15, "Singapur": 16, "Austin": 17,
    "Mexico": 18, "Brasil": 19, "Las Vegas": 20, "Qatar": 21,
    "Abu Dhabi": 22,
}

COLAPINTO_NUMBER = "43"

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FantasyF1/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ERROR: {e}")
        return None

def get_resultado_carrera(round_num):
    """Devuelve (top11, vuelta_rapida, pos_colapinto)"""
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

        top11 = []
        vuelta_rapida = ""
        pos_colapinto = "0"

        for r in results_sorted:
            given = r['Driver'].get('givenName', '')
            family = r['Driver'].get('familyName', '')
            nombre = f"{given} {family}".strip()

            # Top 11
            if len(top11) < 11:
                top11.append(nombre)

            # Vuelta Rápida
            if r.get("FastestLap", {}).get("rank") == "1":
                vuelta_rapida = nombre

            # Colapinto
            number = r['Driver'].get('permanentNumber')
            if number == COLAPINTO_NUMBER or family.lower() == "colapinto":
                pos_colapinto = r.get("position", "0")

        # Si no encontró vuelta rápida, tomar el primero como fallback (por si la API no la marca)
        if not vuelta_rapida and results:
            vuelta_rapida = f"{results[0]['Driver']['givenName']} {results[0]['Driver']['familyName']}"

        return top11, vuelta_rapida, pos_colapinto

    except Exception as e:
        print(f"  ERROR parseando round {round_num}: {e}")
        return None

def main():
    if ARCHIVO_RESULTADOS.exists():
        with open(ARCHIVO_RESULTADOS, encoding="utf-8") as f:
            resultados = json.load(f)
    else:
        resultados = {}

    ahora_iso = datetime.now(timezone.utc).isoformat()

    for carrera, round_num in NOMBRE_A_ROUND.items():
        print(f"Consultando {carrera} (round {round_num})...")

        resultado = get_resultado_carrera(round_num)
        if resultado is None:
            print(f"  → Sin datos aún")
            continue

        top11, vr, pos_col = resultado

        # Se normaliza la clave de carrera (misma normalización que usa fantasy_f1.py
        # al leer este archivo) para que no se acumulen entradas casi-duplicadas como
        # "Gran_bretana" y "Gran Bretana" para la misma carrera.
        resultados[normalizar_nombre_carrera(carrera)] = {
            "resultado_carrera": top11,   # Solo 11 posiciones
            "vuelta_rapida": vr,
            "colapinto": pos_col,
            "_actualizado": ahora_iso,
        }

        print(f"  → OK | P1: {top11[0] if top11 else '?'} | VR: {vr or 'N/A'} | Colapinto: P{pos_col}")

        time.sleep(0.4)

    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\n✅ Listo. Archivo resultados.json actualizado con Top 11.")

if __name__ == "__main__":
    main()