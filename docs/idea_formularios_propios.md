# Idea a futuro: formularios propios en la página (sin Google)

Estado: **idea, no empezada.** Se dejó anotada en octubre de 2026 para
retomarla antes de la temporada 2027.

## El objetivo

Votar (y responder encuestas como la de sugerencias) desde nuestra propia
página, en vez de Google Forms + Google Sheets.

## El problema a resolver

La página vive en GitHub Pages, que solo sirve archivos estáticos: no tiene
dónde guardar lo que alguien manda. Hace falta un servicio que reciba y guarde
las respuestas.

## Propuesta: Supabase (base de datos gratis con login)

```
Hoy:    Google Form → Google Sheets → fetch_votos.py → respuestas/*.csv → ranking
Nuevo:  Formulario en la página → Supabase → fetch_votos.py → respuestas/*.csv → ranking
```

- Solo cambia `fetch_votos.py` (lee de Supabase en vez de Sheets). Los CSV, el
  puntaje, los logros, los avisos y los tests quedan igual.
- Login por mail (link mágico) o con Google: sigue identificando a cada uno por
  su mail, así que `participantes.json` y la regla de "los mails no se
  publican" siguen valiendo.
- Las reglas tienen que vivir **en la base de datos** (Row Level Security),
  no en el JavaScript de la página, porque el código de la página es público:
  - no se puede votar después de la largada;
  - cada uno solo puede leer su propio voto (nadie ve los de los demás antes
    de la carrera).
- La clave pública ("anon key") puede ir en la página. La clave secreta
  ("service_role") va **solo** como Secret de GitHub para el workflow.
- Ojo: en el plan gratis el proyecto se pausa tras una semana sin uso. El
  workflow de domingo y lunes debería mantenerlo despierto.

### Extras que se ganan

- Formulario con la estética de la página y usable desde la app del celular.
- Botón "copiar mi voto anterior" (ataca el 22% de votos perdidos).
- Validar que no se repita un piloto en el top 10.
- "✅ Ya votaste" con tu voto a la vista.
- El recordatorio de WhatsApp puede linkear directo al formulario.

### Alternativas descartadas

- **Cloudflare Workers + D1:** gratis y sólido, pero hay que escribir y
  mantener el servidor a mano.
- **Firebase:** equivalente a Supabase, pero es de Google.
- **Guardar los votos en el repo de GitHub:** el repo es público (se verían los
  votos antes de la carrera) y necesitaría un token secreto en la página.
- **Formspree / Netlify Forms:** solo reenvían por mail, no sirven para votar.

## Plan por etapas

1. **Piloto:** pasar el buzón de sugerencias a una página del sitio guardando
   en Supabase. Si falla, no afecta al ranking.
2. **Votación en paralelo:** el formulario nuevo convive con el Google Form una
   o dos carreras, comparando que den lo mismo.
3. **Cambio definitivo:** arrancar 2027 con el sistema nuevo y retirar Sheets.

Para arrancar hace falta crear la cuenta y el proyecto en supabase.com (a
nombre de quien administra el torneo) y pasar la URL del proyecto y la anon key.
