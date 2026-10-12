"""
Exporta la temporada 2026 completa a un JSON que el sistema nuevo puede cargar.

Lee el repositorio de 2026 (votos en CSV, resultados.json, lista de pilotos y
calendario) y usa SU PROPIO motor de puntaje para anotar cuántos puntos sacó
cada participante en cada carrera. Ese número es la vara: el test
`test_prueba_de_oro.py` carga todo en la base nueva y exige que dé lo mismo,
punto por punto.

Los nombres de pilotos se pasan por la normalización de 2026 ACÁ, una sola
vez. En la base nueva ya no hay nombres que comparar: solo ids.

Uso:
    python scripts/exportar_2026.py ../fantasy-f1-2026
"""

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

SALIDA = Path(__file__).resolve().parent.parent / "datos_2026" / "temporada_2026.json"


def slug(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", nombre)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("origen", help="carpeta del repositorio fantasy-f1-2026")
    args = ap.parse_args()

    origen = Path(args.origen).resolve()
    sys.path.insert(0, str(origen))
    os.chdir(origen)                     # el motor viejo usa rutas relativas

    import pandas as pd
    from f1.config import CALENDARIO, COL_PUESTOS, PILOTOS
    from f1.normalizacion import (normalizar_nombre_carrera, normalizar_piloto,
                                  normalizar_resultados_api)
    from f1.scoring import convertir_posicion_a_numero, procesar_carrera

    seguido = "Franco Colapinto"
    pilotos = list(PILOTOS)
    avisos = []

    def piloto_o_none(valor, contexto):
        texto = "" if pd.isna(valor) else str(valor).strip()
        if not texto:
            return None
        nombre = normalizar_piloto(texto)
        if nombre not in pilotos:
            avisos.append(f"{contexto}: piloto desconocido {texto!r}, se toma como vacío")
            return None
        return nombre

    # Calendario: solo las carreras que se corren, con su número de ronda.
    carreras = []
    for e in CALENDARIO:
        if not e.get("FechaISO"):
            continue
        nombre = normalizar_nombre_carrera(re.sub(r"<[^>]+>", "", e["Carrera"]).strip())
        ronda = int(re.sub(r"\D", "", e["Jornada"]))
        carreras.append({"ronda": ronda, "nombre": nombre, "largada": e["FechaISO"]})
    nombres_carreras = {c["nombre"] for c in carreras}

    with open("resultados.json", encoding="utf-8") as f:
        resultados_crudos = json.load(f)
    resultados_norm = normalizar_resultados_api(json.loads(json.dumps(resultados_crudos)))

    resultados = {}
    for carrera, datos in resultados_norm.items():
        if not datos.get("resultado_carrera"):
            continue
        clasificacion = []
        for pos, nombre in enumerate(datos["resultado_carrera"], 1):
            if nombre not in pilotos:
                avisos.append(f"{carrera}: el resultado trae {nombre!r}, se agrega a pilotos")
                pilotos.append(nombre)
            clasificacion.append({"piloto": nombre, "posicion": pos})
        col = datos.get("colapinto", 0)
        try:
            col = convertir_posicion_a_numero(col) if isinstance(col, str) else int(col or 0)
        except (ValueError, TypeError):
            col = 0
        if seguido not in datos["resultado_carrera"]:
            clasificacion.append({"piloto": seguido, "posicion": col or None})
        vr = datos.get("vuelta_rapida") or None
        if vr and vr not in pilotos:
            avisos.append(f"{carrera}: vuelta rápida de {vr!r}, desconocido")
            vr = None
        resultados[carrera] = {"clasificacion": clasificacion, "vuelta_rapida": vr}

    # Votos y puntaje esperado, carrera por carrera, igual que f1/main.py.
    votos, esperado, participantes = [], {}, set()
    for archivo in sorted(os.listdir("respuestas")):
        if not archivo.endswith(".csv"):
            continue
        carrera = normalizar_nombre_carrera(archivo.replace("respuestas_", "").replace(".csv", ""))
        if carrera not in nombres_carreras:
            avisos.append(f"{archivo}: la carrera {carrera!r} no está en el calendario")
            continue
        df = pd.read_csv(Path("respuestas") / archivo)
        df.columns = df.columns.str.strip().str.replace(r"\s+", " ", regex=True)

        if df["Participante"].duplicated().any():
            avisos.append(f"{archivo}: hay participantes con más de un voto")

        for _, fila in df.iterrows():
            apodo = str(fila["Participante"]).strip()
            participantes.add(apodo)
            ctx = f"{carrera}/{apodo}"
            pos_seg = str(fila.get("Franco Colapinto", "")).strip()
            try:
                pos_seg = convertir_posicion_a_numero(pos_seg) if pos_seg and pos_seg != "nan" else None
            except (ValueError, TypeError):
                pos_seg = None
            votos.append({
                "carrera": carrera,
                "participante": apodo,
                "top10": [piloto_o_none(fila.get(c), ctx) for c in COL_PUESTOS],
                "vuelta_rapida": piloto_o_none(fila.get("Vuelta Rápida"), ctx),
                "pos_seguido": pos_seg,
            })

        if carrera in resultados_norm and resultados_norm[carrera].get("resultado_carrera"):
            ranking, _ = procesar_carrera(carrera, str(Path("respuestas") / archivo),
                                          resultados_norm[carrera])
            esperado[carrera] = {r["Participante"]: int(r["Puntos"])
                                 for _, r in ranking.iterrows()}

    salida = {
        "temporada": 2026,
        "piloto_seguido": seguido,
        "pilotos": [{"codigo_api": slug(p), "nombre": p} for p in pilotos],
        "carreras": carreras,
        "participantes": sorted(participantes),
        "votos": votos,
        "resultados": resultados,
        "esperado": esperado,
    }
    # Todo en códigos, no en nombres: así la carga no compara texto.
    codigo = {p: slug(p) for p in pilotos}
    for v in votos:
        v["top10"] = [codigo.get(p) for p in v["top10"]]
        v["vuelta_rapida"] = codigo.get(v["vuelta_rapida"])
    for r in resultados.values():
        for e in r["clasificacion"]:
            e["piloto"] = codigo[e["piloto"]]
        r["vuelta_rapida"] = codigo.get(r["vuelta_rapida"])

    SALIDA.parent.mkdir(exist_ok=True)
    SALIDA.write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(carreras)} carreras, {len(resultados)} con resultado, "
          f"{len(votos)} votos, {len(participantes)} participantes")
    for a in avisos:
        print("AVISO:", a)
    print(f"-> {SALIDA}")


if __name__ == "__main__":
    main()
