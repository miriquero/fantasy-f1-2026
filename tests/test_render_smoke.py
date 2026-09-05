"""
Smoke test de punta a punta: corre el pipeline completo contra los datos
reales del repo (respuestas/*.csv + resultados.json) y valida que el HTML
generado no tenga fragmentos de template sin resolver ni datos faltantes.

No depende de red ni de credenciales: usa los archivos ya versionados.
"""

import re

import f1.main


def test_pipeline_completo_genera_html_valido(tmp_path, monkeypatch):
    salida = tmp_path / "ranking_f1_test.html"
    monkeypatch.setattr(f1.main, "ARCHIVO_SALIDA_HTML", str(salida))

    f1.main.main()

    assert salida.exists(), "main() no escribió el archivo de salida"
    html = salida.read_text(encoding="utf-8")

    # No debe quedar ningún placeholder de Jinja2 sin resolver
    assert not re.search(r"{{\s*\w+\s*}}", html), "quedó una variable de Jinja2 sin renderizar"
    assert "{%" not in html, "quedó un tag de Jinja2 sin renderizar"

    # Estructura básica del documento
    assert html.startswith("<!DOCTYPE html>")
    assert "</html>" in html
    assert "PUNTOS" in html.upper()

    # Participantes reales del torneo deben aparecer en el ranking
    assert "miriquero@gmail.com" in html
    assert "alinaiaraceleste@gmail.com" in html
