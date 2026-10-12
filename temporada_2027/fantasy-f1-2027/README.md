# Torneo F1 familiar — 2027

El torneo, funcionando solo. Se vota desde la página, la votación se abre y
se cierra sola con cada carrera, los resultados llegan de la API y los puntos
se calculan sin que nadie toque nada.

El diseño completo y el porqué de cada decisión están en
`ARQUITECTURA_2027.md` (en el repositorio de 2026, carpeta `temporada_2027/`).

## Qué hay

```
supabase/migrations/   La base de datos: tablas, reglas, cálculo, seguridad, reloj.
  ..._esquema.sql      Tablas. Las reglas del juego son datos (tabla temporadas).
  ..._puntaje.sql      Cálculo de puntos y vistas del ranking.
  ..._ciclo.sql        votar(), resultados, avance automático de cada carrera.
  ..._seguridad.sql    Qué puede ver y hacer la página.
  ..._reloj.sql        pg_cron: corre avanzar_estados() cada 5 minutos.
scripts/
  exportar_2026.py     Saca la temporada 2026 del repo viejo, con los puntos que dio.
  cargar_temporada.py  La carga en una base (tests o Supabase).
datos_2026/            La temporada 2026 exportada.
tests/                 Corren contra un Postgres real.
```

## Estado

| Parte | Estado |
|---|---|
| Base de datos y reglas | Hecha |
| Prueba de oro: 2026 entera da los mismos puntos | **En verde** |
| Votación con control de horario, duplicados y permisos | Hecha |
| Ciclo de cada carrera y recordatorios | Hecho |
| Correcciones de la FIA con historial | Hecho |
| Traer calendario y resultados de la API | Pendiente |
| Mandar los avisos por WhatsApp | Pendiente |
| Login | **En discusión** (todo pasa por `participante_actual()`, así que se decide después sin tocar el resto) |
| Página | Pendiente |

## Correr los tests

Hace falta un Postgres 16. Con Docker:

```
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:16
pip install -r requirements-dev.txt
pytest
```

`DATABASE_URL` apunta a otro Postgres si hace falta.
