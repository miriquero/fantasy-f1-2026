"""Que todo el código del proyecto al menos compile e importe.

Esto existe por un error real: al editar los mensajes de notificar.py quedó una
cadena partida por la mitad y el archivo dejó de ser Python válido. Ninguna
prueba lo tocaba, así que la suite seguía en verde y el archivo roto llegó a
producción. El bot habría fallado al mandar cualquier aviso.

Es la prueba más barata que existe y cubre a todos los archivos, incluidos los
que nadie más testea.
"""

import ast
import importlib
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

ARCHIVOS = sorted(
    p for p in list(RAIZ.glob("*.py")) + list(RAIZ.glob("f1/*.py"))
    if "__pycache__" not in str(p)
)

# Todo lo que el workflow ejecuta con `python <script>.py`.
EJECUTABLES = ["fantasy_f1", "fetch_votos", "fetch_resultados",
               "notificar", "recordar_votos"]


def test_hay_archivos_para_revisar():
    # Si el glob deja de encontrar nada, los tests de abajo pasarían vacíos.
    assert len(ARCHIVOS) >= 10


@pytest.mark.parametrize("ruta", ARCHIVOS, ids=lambda p: p.name)
def test_el_archivo_es_python_valido(ruta):
    try:
        ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    except SyntaxError as e:
        pytest.fail(f"{ruta.relative_to(RAIZ)} no compila: línea {e.lineno}: {e.msg}")


@pytest.mark.parametrize("modulo", EJECUTABLES)
def test_los_scripts_del_workflow_importan(modulo):
    # Importar es más fuerte que compilar: agarra también los imports rotos,
    # que es como se rompió fetch_resultados.py cuando el paquete f1/ no existía.
    importlib.import_module(modulo)


@pytest.mark.parametrize("tipo", ["exito", "recordatorio", "tardios",
                                  "penalidad", "error"])
def test_cada_tipo_de_aviso_arma_un_mensaje(tipo, monkeypatch):
    """Los cinco mensajes se arman sin romperse y dicen algo."""
    import notificar

    enviados = []
    monkeypatch.setattr(notificar, "enviar_whatsapp",
                        lambda m: enviados.append(m) or True)
    monkeypatch.setattr("sys.argv", ["notificar.py", tipo, "detalle de prueba"])
    with pytest.raises(SystemExit) as salida:
        notificar.main()

    assert salida.value.code == 0
    assert len(enviados) == 1
    assert "detalle de prueba" in enviados[0]
    assert len(enviados[0].strip()) > 20
