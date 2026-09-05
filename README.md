# Fantasy F1 2026

Torneo familiar de predicciones de Fórmula 1. Cada participante predice el
top 10 de cada carrera en un Google Form; el sistema calcula los puntos, el
ranking acumulado y un panel de logros ("badges"), y publica todo como una
página estática en GitHub Pages.

Sitio publicado: https://miriquero.github.io/fantasy-f1-2026/ranking_f1.html

## Cómo funciona el pipeline

```
Google Form → Google Sheets → fetch_votos.py → respuestas/*.csv
                                                       │
API Jolpica (resultados reales) → fetch_resultados.py → resultados.json
                                                       │
                                                       ▼
                                              fantasy_f1.py (f1/)
                                                       │
                                                       ▼
                                              ranking_f1.html
                                                       │
                                                       ▼
                                          GitHub Pages (commit automático)
```

Un GitHub Action (`.github/workflows/post_carrera.yml`) corre este pipeline
dos veces al día: trae los votos nuevos, trae los resultados de carrera si ya
salieron, recalcula el ranking, commitea `ranking_f1.html` y `resultados.json`
si hubo cambios, y manda un aviso por WhatsApp (CallMeBot).

## Estructura del código

- `fantasy_f1.py` — punto de entrada (wrapper delgado, solo llama a `f1.main.main()`).
  Se mantiene en la raíz para que el workflow de GitHub Actions no tenga que cambiar.
- `fetch_votos.py` — lee las respuestas del Google Form desde Sheets y genera un CSV por carrera.
- `fetch_resultados.py` — consulta la API Jolpica y actualiza `resultados.json`.
- `notificar.py` — manda el aviso por WhatsApp al terminar el workflow.
- `f1/` — paquete con toda la lógica de cálculo y render:
  - `config.py` — pilotos, calendario de la temporada, rutas de archivos.
  - `normalizacion.py` — traduce variantes de nombres de pilotos/carreras (con o sin tilde, alias de la API) a los nombres canónicos.
  - `scoring.py` — calcula puntos por carrera y arma el ranking acumulado.
  - `badges.py` — sistema de logros: definición de los 15 badges y quién los desbloqueó.
  - `calendario.py` — orden de carreras y panel visual del calendario.
  - `charts.py` — gráficos (matplotlib) embebidos como PNG en base64.
  - `perfiles.py` — panel de perfiles individuales, selector, Hall of Fame y estadísticas.
  - `validacion.py` — valida la estructura de `resultados.json` antes de calcular.
  - `render.py` — arma todos los fragmentos de HTML y los renderiza con Jinja2.
  - `templates/` — el HTML, CSS y JS del sitio, como archivos reales (no strings de Python).
- `tests/` — suite de pytest (normalización, puntaje, badges, y un smoke test de punta a punta).

## Correrlo localmente

```bash
pip install -r requirements-dev.txt
python fantasy_f1.py
```

Esto lee `respuestas/*.csv` y `resultados.json` (ya versionados en el repo) y
genera `ranking_f1.html` en la raíz — abrilo directo en el navegador.

Para correr los tests:

```bash
pytest tests/ -v
```

## Variables de entorno / secrets

Usados por el workflow de GitHub Actions (configurados como Secrets del repo,
nunca committeados):

- `GOOGLE_SHEETS_CREDENTIALS` — JSON de la service account de Google (para `fetch_votos.py`).
- `CALLMEBOT_PHONE` / `CALLMEBOT_APIKEY` — para el aviso por WhatsApp (`notificar.py`).

Para correr `fetch_votos.py` en forma local hace falta además el archivo de
credenciales de la service account (ver `fetch_votos.py` para el nombre de
archivo esperado) — no se versiona, está en `.gitignore`.
