# -*- coding: utf-8 -*-
"""Como los scripts le cuentan al workflow que pasó algo digno de avisar.

Cada script del pipeline corre en su propio paso de GitHub Actions, asi que no
pueden pasarse datos en memoria. Dejan un archivo en `avisos/` y el paso
siguiente mira si existe. La carpeta es efimera: vive lo que dura la corrida y
no se versiona.

Aparte hay un estado que SI persiste, `estado_avisos.json`, para no repetir el
mismo aviso en cada corrida. Hace falta solo para los votos tardios: el voto
queda en el Google Form para siempre, asi que sin memoria se avisaria dos
veces por dia de por vida. Las penalidades no lo necesitan, porque
fetch_resultados.py solo reporta un cambio cuando el resultado difiere del que
ya estaba guardado, y despues lo guarda.
"""

import json
from pathlib import Path

CARPETA = Path("avisos")
ESTADO = Path("estado_avisos.json")


def anotar(nombre: str, texto: str) -> None:
    """Deja un aviso para que lo levante el paso siguiente del workflow."""
    if not texto.strip():
        return
    CARPETA.mkdir(exist_ok=True)
    (CARPETA / f"{nombre}.txt").write_text(texto.strip() + "\n",
                                           encoding="utf-8", newline="\n")


def leer_estado() -> dict:
    """Lo que ya se avisó en corridas anteriores."""
    if ESTADO.exists():
        try:
            return json.loads(ESTADO.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            # Un archivo corrupto no puede frenar el pipeline: se arranca de
            # cero y a lo sumo se repite un aviso.
            return {}
    return {}


def guardar_estado(estado: dict) -> None:
    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8", newline="\n")


def ya_avisado(estado: dict, clave: str, item: str) -> bool:
    return item in estado.get(clave, [])


def marcar_avisado(estado: dict, clave: str, item: str) -> None:
    estado.setdefault(clave, [])
    if item not in estado[clave]:
        estado[clave].append(item)
