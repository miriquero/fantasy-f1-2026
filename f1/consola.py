# -*- coding: utf-8 -*-
"""Deja la consola en UTF-8 para poder imprimir emoji y acentos."""

import sys


def configurar_salida_utf8() -> None:
    """Fuerza UTF-8 en stdout/stderr.

    En Windows la consola usa cp1252 por defecto y no sabe representar los
    emoji de los mensajes ("✅", "🏁", "→"). Sin esto, el script muere con
    UnicodeEncodeError DESPUES de haber hecho todo el trabajo, solo por no
    poder imprimir el cartel final. En Linux (GitHub Actions) ya es UTF-8 y
    esta llamada no cambia nada.
    """
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")
