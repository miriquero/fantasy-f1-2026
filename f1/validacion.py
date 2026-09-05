# -*- coding: utf-8 -*-
"""Valida la estructura de resultados.json antes de calcular."""

from typing import Dict

from .config import ARCHIVO_RESULTADOS, PILOTOS


CAMPOS_REQUERIDOS = ["resultado_carrera", "vuelta_rapida", "colapinto"]


def validar_resultados(resultados_por_carrera: Dict) -> bool:
    """
    Valida que el archivo resultados.json tenga la estructura correcta.
    Por cada carrera verifica que existan y tengan contenido los tres campos
    requeridos: resultado_carrera, vuelta_rapida y colapinto.

    Retorna True si todo está bien, False si hay errores bloqueantes.
    Imprime advertencias para problemas menores (campos vacíos en carreras
    que todavía no se disputaron) y errores para problemas que impedirían
    un cálculo correcto.
    """
    if not isinstance(resultados_por_carrera, dict):
        print(f"ERROR: {ARCHIVO_RESULTADOS} debe ser un objeto JSON, no {type(resultados_por_carrera).__name__}.")
        return False

    if not resultados_por_carrera:
        print(f"ERROR: {ARCHIVO_RESULTADOS} está vacío, no hay carreras para procesar.")
        return False

    errores = []

    for carrera, datos in resultados_por_carrera.items():
        if not isinstance(datos, dict):
            errores.append(f"  · [{carrera}] el valor debe ser un objeto JSON, no {type(datos).__name__}.")
            continue

        # Campos faltantes (la clave no existe)
        faltantes = [c for c in CAMPOS_REQUERIDOS if c not in datos]
        if faltantes:
            errores.append(
                f"  · [{carrera}] faltan los campos: {', '.join(faltantes)}.\n"
                f"    Estructura esperada: {{\"resultado_carrera\": [...], \"vuelta_rapida\": \"Piloto\", \"colapinto\": 14}}"
            )
            continue

        # resultado_carrera: debe ser una lista con al menos 10 pilotos
        rc = datos["resultado_carrera"]
        if not isinstance(rc, list):
            errores.append(f"  · [{carrera}] 'resultado_carrera' debe ser una lista, no {type(rc).__name__}.")
        elif len(rc) == 0:
            # Lista vacía = carrera aún no disputada, solo advertencia
            print(f"Advertencia: [{carrera}] 'resultado_carrera' está vacío (¿carrera pendiente?).")
        elif len(rc) < 10:
            errores.append(
                f"  · [{carrera}] 'resultado_carrera' tiene {len(rc)} pilotos, se esperan al menos 10."
            )
        else:
            # Verificar que los pilotos estén en la lista oficial
            desconocidos = [p for p in rc if p not in PILOTOS]
            if desconocidos:
                errores.append(
                    f"  · [{carrera}] pilotos no reconocidos en 'resultado_carrera': {desconocidos}.\n"
                    f"    Revisá mayúsculas/tildes contra la lista PILOTOS del código, o agregá un alias\n"
                    f"    en ALIASES_PILOTOS si es una variante nueva que devuelve la API."
                )

        # vuelta_rapida: string no vacío
        vr = datos["vuelta_rapida"]
        if not isinstance(vr, str):
            errores.append(f"  · [{carrera}] 'vuelta_rapida' debe ser un string, no {type(vr).__name__}.")
        elif vr.strip() == "":
            print(f"Advertencia: [{carrera}] 'vuelta_rapida' está vacío — no se otorgarán puntos por vuelta rápida.")
        elif vr not in PILOTOS:
            errores.append(
                f"  · [{carrera}] piloto de vuelta rápida no reconocido: \"{vr}\".\n"
                f"    Revisá mayúsculas/tildes contra la lista PILOTOS del código, o agregá un alias\n"
                f"    en ALIASES_PILOTOS si es una variante nueva que devuelve la API."
            )

        # colapinto: número entero entre 1 y 20 (o 0 si no clasificó/abandonó)
        col = datos["colapinto"]
        # Aceptar tanto int como string numérico (ej: 14 o "14")
        try:
            col_int = int(col)
        except (ValueError, TypeError):
            errores.append(
                f"  · [{carrera}] 'colapinto' debe ser un número (posición), no {type(col).__name__}.\n"
                f"    Ejemplo: 14 si terminó 14°, 0 si no clasificó o abandonó."
            )
            col_int = None
        if col_int is not None and not (0 <= col_int <= 20):
            errores.append(f"  · [{carrera}] 'colapinto' tiene valor inválido: {col}. Debe estar entre 0 y 20.")

    if errores:
        print(f"\n❌ Se encontraron {len(errores)} error(es) en {ARCHIVO_RESULTADOS}:\n")
        for e in errores:
            print(e)
        print(f"\nCorregí los errores anteriores y volvé a correr el script.\n")
        return False

    print(f"✅ {ARCHIVO_RESULTADOS} validado correctamente ({len(resultados_por_carrera)} carrera(s) en el archivo).")
    return True
