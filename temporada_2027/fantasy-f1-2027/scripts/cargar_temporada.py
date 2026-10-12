"""
Carga en la base una temporada exportada por exportar_2026.py.

Sirve para dos cosas: la prueba de oro (los tests la usan sobre una base
local) y la migración real a Supabase.

Uso:
    DATABASE_URL=postgresql://... python scripts/cargar_temporada.py datos_2026/temporada_2026.json
"""

import json
import os
import sys

import psycopg
from psycopg.types.json import Jsonb


def cargar(conn: psycopg.Connection, datos: dict) -> None:
    """Carga todo en una sola transacción: o entra entera o no entra nada."""
    anio = datos["temporada"]
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("insert into temporadas (anio) values (%s)", (anio,))

        piloto_id = {}
        for p in datos["pilotos"]:
            cur.execute(
                "insert into pilotos (temporada, codigo_api, nombre) values (%s, %s, %s) returning id",
                (anio, p["codigo_api"], p["nombre"]))
            piloto_id[p["codigo_api"]] = cur.fetchone()[0]

        seguido = next(p["codigo_api"] for p in datos["pilotos"]
                       if p["nombre"] == datos["piloto_seguido"])
        cur.execute("update temporadas set piloto_seguido_id = %s where anio = %s",
                    (piloto_id[seguido], anio))

        participante_id = {}
        for apodo in datos["participantes"]:
            cur.execute(
                "insert into participantes (apodo) values (%s) "
                "on conflict (apodo) do update set apodo = excluded.apodo returning id",
                (apodo,))
            participante_id[apodo] = cur.fetchone()[0]

        carrera_id = {}
        for c in datos["carreras"]:
            cur.execute(
                "insert into carreras (temporada, ronda, nombre, largada) "
                "values (%s, %s, %s, %s) returning id",
                (anio, c["ronda"], c["nombre"], c["largada"]))
            carrera_id[c["nombre"]] = cur.fetchone()[0]

        # Los votos van directo a la tabla: son carreras ya cerradas y votar()
        # las rechazaría. Primero los votos, después los resultados, porque
        # cargar un resultado es lo que calcula los puntos.
        for v in datos["votos"]:
            cur.execute(
                "insert into votos (participante_id, carrera_id, top10, vuelta_rapida_id, pos_seguido) "
                "values (%s, %s, %s, %s, %s)",
                (participante_id[v["participante"]], carrera_id[v["carrera"]],
                 [piloto_id.get(p) if p else None for p in v["top10"]],
                 piloto_id.get(v["vuelta_rapida"]) if v["vuelta_rapida"] else None,
                 v["pos_seguido"]))

        for carrera, r in datos["resultados"].items():
            cur.execute("select registrar_resultado(%s, %s, %s, 'importado 2026')",
                        (carrera_id[carrera], Jsonb(r["clasificacion"]), r["vuelta_rapida"]))

        cur.execute("select avanzar_estados()")

        # Todo lo que la carga dejó en la cola de avisos es historia: no se
        # manda ningún WhatsApp por carreras de hace meses.
        cur.execute("update eventos set enviado = now() where enviado is null")


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        datos = json.load(f)
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        cargar(conn, datos)
    print(f"Temporada {datos['temporada']} cargada.")


if __name__ == "__main__":
    main()
