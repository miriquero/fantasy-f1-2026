"""
fetch_resultados_2027.py
------------------------
Versión Autónoma 2027 usando FastF1.
Adiós a las demoras de Jolpica. Se conecta directamente a la telemetría de la FIA
y obtiene los resultados al instante después de la carrera.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
import fastf1

# Activar caché de FastF1 para no descargar telemetría repetida
fastf1.Cache.enable_cache('fastf1_cache')

ARCHIVO_RESULTADOS = Path("../resultados.json")
COLAPINTO_NUMBER = "43" # Actualizar si Franco cambia de número en 2027
YEAR = 2027

def obtener_resultados_rapidos(round_num):
    """
    Se conecta a los servidores de F1. 
    Si la carrera no terminó, fallará o devolverá resultados incompletos.
    """
    try:
        # 'R' significa Race (Carrera)
        session = fastf1.get_session(YEAR, round_num, 'R')
        
        # load() descarga los datos. Apagamos telemetría pesada para que sea rápido.
        session.load(telemetry=False, weather=False, messages=False)
    except Exception as e:
        print(f"  → La carrera {round_num} aún no está disponible en Live Timing.")
        return None
        
    resultados = session.results
    if resultados.empty or session.session_status != 'Finalised':
        return None
        
    top11 = []
    pos_colapinto = "0"
    
    # Extraer la vuelta rápida de la sesión
    fastest_lap_driver = ""
    try:
        fastest_lap = session.laps.pick_fastest()
        fastest_lap_driver = f"{fastest_lap['Driver']}"
    except:
        pass

    for index, row in resultados.iterrows():
        nombre = f"{row['FirstName']} {row['LastName']}"
        posicion = str(row['Position']).split('.')[0] # 1.0 -> 1
        
        # Guardar solo el Top 11 (para la regla de los 5 puntos de consuelo)
        if len(top11) < 11:
            top11.append(nombre)
            
        # Revisar si es Colapinto
        if str(row['DriverNumber']) == COLAPINTO_NUMBER or "Colapinto" in nombre:
            pos_colapinto = posicion
            
        # Mapear la vuelta rápida (FastF1 guarda la sigla del piloto)
        if fastest_lap_driver == row['Abbreviation']:
            fastest_lap_driver = nombre
            
    return top11, fastest_lap_driver, pos_colapinto

def main():
    if ARCHIVO_RESULTADOS.exists():
        with open(ARCHIVO_RESULTADOS, encoding="utf-8") as f:
            db_resultados = json.load(f)
    else:
        db_resultados = {}

    ahora_iso = datetime.now(timezone.utc).isoformat()
    
    # Obtener el calendario oficial directamente desde FastF1
    calendario = fastf1.get_event_schedule(YEAR)
    carreras = calendario[calendario['EventFormat'] != 'testing']
    
    print(f"Calendario FastF1: {len(carreras)} carreras encontradas para {YEAR}.")

    for index, evento in carreras.iterrows():
        round_num = evento['RoundNumber']
        carrera_nombre = evento['EventName']
        
        # Normalizar el nombre para guardarlo en el JSON
        clave = carrera_nombre.lower().replace(" grand prix", "").replace(" ", "_")
        
        print(f"Consultando {carrera_nombre} (Round {round_num})...")
        
        resultado = obtener_resultados_rapidos(round_num)
        if not resultado:
            continue
            
        top11, vr, pos_col = resultado
        
        nuevo = {
            "resultado_carrera": top11,
            "vuelta_rapida": vr,
            "colapinto": pos_col,
            "_actualizado": ahora_iso
        }
        
        # Solo actualizamos si cambió algo
        anterior = db_resultados.get(clave, {})
        if anterior.get("resultado_carrera") == top11:
            print(f"  → Sin cambios | P1: {top11[0]}")
            continue
            
        db_resultados[clave] = nuevo
        print(f"  → ¡DATOS NUEVOS! | P1: {top11[0]} | VR: {vr} | Colapinto: P{pos_col}")

    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump(db_resultados, f, ensure_ascii=False, indent=2)
        f.write("\n")

if __name__ == "__main__":
    main()
