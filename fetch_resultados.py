"""
fetch_resultados.py
-------------------
Consulta la API Jolpica y guarda solo lo necesario:
- Top 11 de la carrera
- Vuelta rápida
- Posición de Colapinto
"""

import json
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from f1.config import CALENDARIO
from f1.consola import configurar_salida_utf8
from f1.normalizacion import normalizar_nombre_carrera

ARCHIVO_RESULTADOS = Path("resultados.json")
BASE_URL = "https://api.jolpi.ca/ergast/f1/2026"

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

def fetch_calendario_api():
    """Calendario de la temporada segun la API: {fecha_utc: (round, nombre)}."""
    data = fetch_json(f"{BASE_URL}.json?limit=40")
    try:
        carreras = data["MRData"]["RaceTable"]["Races"]
    except (KeyError, TypeError):
        return None
    return {c["date"]: (int(c["round"]), c["raceName"]) for c in carreras}


def rounds_del_torneo(calendario_api):
    """Empareja cada carrera del torneo con su round real, por fecha.

    Antes los numeros de round estaban escritos a mano aca, y se desfasaron:
    la FIA sumo el "Bahrain Grand Prix in Malaysia" como round 16 y todo lo
    posterior corrio un lugar. Con la tabla vieja, el 11 de octubre el script
    hubiera pedido el round 16, recibido la carrera de Malasia y guardado esos
    resultados bajo el nombre "Singapur", puntuando a todos contra la carrera
    equivocada sin que saltara ningun error.

    Emparejar por fecha se arregla solo la proxima vez que cambie el calendario.
    """
    mapa = {}
    for entrada in CALENDARIO:
        iso = entrada.get("FechaISO")
        if not iso:
            continue                       # carrera tachada del torneo
        nombre = re.sub(r"<[^>]+>", "", entrada["Carrera"]).strip()
        fecha = datetime.fromisoformat(iso).astimezone(timezone.utc).date().isoformat()
        if fecha in calendario_api:
            mapa[nombre] = calendario_api[fecha][0]
        else:
            print(f"  AVISO: '{nombre}' ({fecha}) no figura en el calendario de la API.")
    return mapa


def main():
    if ARCHIVO_RESULTADOS.exists():
        with open(ARCHIVO_RESULTADOS, encoding="utf-8") as f:
            resultados = json.load(f)
    else:
        resultados = {}

    ahora_iso = datetime.now(timezone.utc).isoformat()

    calendario_api = fetch_calendario_api()
    if not calendario_api:
        print("No se pudo leer el calendario de la API. No se toca resultados.json.")
        return
    print(f"Calendario de la API: {len(calendario_api)} carreras.")

    for carrera, round_num in rounds_del_torneo(calendario_api).items():
        print(f"Consultando {carrera} (round {round_num})...")

        resultado = get_resultado_carrera(round_num)
        if resultado is None:
            print(f"  → Sin datos aún")
            continue

        top11, vr, pos_col = resultado

        # Se normaliza la clave de carrera (misma normalización que usa fantasy_f1.py
        # al leer este archivo) para que no se acumulen entradas casi-duplicadas como
        # "Gran_bretana" y "Gran Bretana" para la misma carrera.
        clave = normalizar_nombre_carrera(carrera)
        nuevo = {
            "resultado_carrera": top11,   # Solo 11 posiciones
            "vuelta_rapida": vr,
            "colapinto": pos_col,
        }

        anterior = resultados.get(clave, {})
        if all(anterior.get(k) == v for k, v in nuevo.items()):
            # Nada cambió: no se toca "_actualizado". Antes se reescribia en
            # cada corrida, asi que el diff de resultados.json mostraba las 22
            # carreras tocadas aunque no hubiera pasado nada y no se podia ver
            # cual habia cambiado de verdad. (El commit se hace igual: el HTML
            # lleva la hora de generacion y cambia siempre.)
            print(f"  → sin cambios | P1: {top11[0] if top11 else '?'}")
            time.sleep(0.4)
            continue

        nuevo["_actualizado"] = ahora_iso
        resultados[clave] = nuevo
        print(f"  → OK | P1: {top11[0] if top11 else '?'} | VR: {vr or 'N/A'} | Colapinto: P{pos_col}")

        time.sleep(0.4)

    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\n✅ Listo. Archivo resultados.json actualizado con Top 11.")

if __name__ == "__main__":
    configurar_salida_utf8()
    main()