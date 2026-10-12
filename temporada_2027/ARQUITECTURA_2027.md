# Arquitectura 2027 — revisión y propuesta

Objetivo: que el torneo funcione solo de punta a punta. Cada uno vota desde la
misma página; la votación se abre y se cierra sola con cada carrera; los
resultados llegan de una API; los puntos, el ranking y los avisos salen sin que
nadie toque nada. Y si algo falla, que lo detecte el sistema antes que la
familia.

Este documento tiene dos partes: qué está flojo hoy y por qué, y cómo lo
armaríamos para 2027. Las decisiones de reglas (Colapinto, faltazos, logros)
están en `PLAN_2027.md` y no se repiten acá.

---

## Parte 1 — Qué está flojo hoy

### Cómo funciona hoy

```
Google Form ──► Google Sheet ──┐
                               │  GitHub Actions (cron, Python)
Jolpica API ───────────────────┼──► CSVs + resultados.json commiteados en git
                               │          │
                               │          ▼
                               │   genera ranking_f1.html (4.500 líneas)
                               │          │
                               │          ▼
                               └──► GitHub Pages      CallMeBot ──► 1 teléfono
```

Funciona, y en 2026 lo fuimos blindando a fuerza de golpes. Pero tiene siete
puntos débiles de diseño. No son bugs puntuales: son lugares donde, por cómo
está armado, van a seguir apareciendo bugs.

### 1. El reloj no es confiable

Todo depende del cron de GitHub Actions. Lo medimos: atrasa entre 1 h 40 y
5 h 24, y a veces directamente no corre. En Azerbaiyán hubo que correr todo a
mano. GitHub además **desactiva los crons de un repo público después de 60 días
sin actividad**: entre Abu Dhabi y Australia hay más de 90 días sin carreras,
así que en marzo el sistema puede arrancar apagado y nadie se entera.

**Gravedad: alta.** Es la causa raíz de la mayoría de los "no se corrieron los
puntos".

### 2. Git hace de base de datos

Los votos, los resultados y el estado de los avisos viven en archivos
commiteados. Consecuencias:

- **Dos workflows escriben al mismo repo sin coordinarse.** El recordatorio y
  el post-carrera hacen `git push` sin `pull` previo y sin grupo de
  `concurrency`. Si coinciden, el segundo push es rechazado y el workflow muere
  con "error" aunque los puntos estuvieran bien.
- Los commits del bot no disparan CI, por eso CI estuvo rojo una semana sin que
  nadie lo viera (PLAN_2027 §3.3).
- El historial se llena de "Auto: actualización" y no hay forma de consultar
  nada ("¿qué votó Fulano en Mónaco?") sin abrir CSVs.

### 3. La planilla es la fuente de verdad de los votos

- **No hay identidad real**: el votante se identifica por el mail que escribe
  el form. No hay forma de impedir que alguien vote por otro.
- **Editar una fila no deja rastro** (pasó en Azerbaiyán, PLAN_2027 §3.4).
- **El form no se cierra solo**: el corte de votos se aplica después, al leer,
  comparando marcas de tiempo.
- **Las opciones están escritas a mano** y no coinciden con las del torneo
  (Hülkenberg con diéresis: 16 predicciones mal puntuadas).
- No valida nada: se puede poner el mismo piloto en P1 y en P4.

### 4. La página no está viva

`ranking_f1.html` es una foto que se regenera entera en cada corrida. Entre
corrida y corrida, lo que se ve está desactualizado, y la página no puede
recibir nada (por eso hace falta el form aparte).

### 5. El puntaje devuelve texto, no datos

Los logros se enteran de qué acertó cada uno **leyendo el texto** que escribe
el cálculo. Ya rompió tres veces (PLAN_2027 §3.5). Cualquier pantalla nueva
(la pestaña Final, "Tu temporada", "¿Y si…?") tiene el mismo problema.

### 6. Los avisos dependen de un solo teléfono

CallMeBot es un servicio gratuito no oficial, y manda **a un solo número**
(`CALLMEBOT_PHONE`). La familia no recibe nada directo: depende de que vos
reenvíes. Si CallMeBot cae o cambia, no hay plan B.

### 7. Nadie vigila al vigilante

Si un workflow no corre, no hay aviso: el silencio parece normalidad. No existe
un chequeo del tipo "terminó la carrera hace 6 horas y todavía no hay
resultados".

### Lo que está bien y hay que conservar

- **El motor de puntaje y los 216 tests.** Las reglas están auditadas y fijadas.
- **La normalización de nombres y el emparejamiento por fecha** (no por round).
- **Los avisos de penalidad FIA, voto tardío y carrera desconocida.** Son
  buenas ideas; en 2027 pasan a ser chequeos automáticos de la base.
- **El diseño de la página**, el PWA y el sprite.
- **Todo el archivo de 2026** (votos crudos + resultados): sirve para migrar y,
  sobre todo, para probar el sistema nuevo (ver Parte 2, "La prueba de oro").

---

## Parte 2 — Cómo lo armaríamos para 2027

### La idea en una línea

Pasar de "un script que corre de vez en cuando y genera una foto" a **una base
de datos con reglas adentro y una página que lee y escribe en vivo**.

```
                        ┌──────────────────────── Supabase ───────────────────────┐
  Página (PWA)          │                                                         │
  ─ login con mail ────►│  Auth            Postgres                   pg_cron      │
  ─ vota ──────────────►│                  ├─ carreras  (estado)  ◄── cada 5 min:  │
  ─ ve ranking en vivo ◄│  Reglas de       ├─ pilotos                 abrir/cerrar │
                        │  acceso (RLS):   ├─ votos  + auditoría      votación     │
                        │  "solo tu voto,  ├─ resultados + revisiones              │
                        │   solo antes de  ├─ puntajes (datos, no texto)           │
                        │   la largada"    └─ avisos enviados                      │
                        │                                         Edge Functions:  │
                        │                                         ─ traer calendario│
                        │                                         ─ traer resultados│◄── Jolpica
                        │                                         ─ mandar avisos   │◄── OpenF1 (respaldo)
                        └──────────────────────────────────────────────┬────────────┘
                                                                       ▼
                                                     Telegram / WhatsApp / push del navegador
```

### Por qué Supabase

Para 10 personas y 24 carreras, cualquier opción seria es gratis. Elegí
Supabase porque resuelve en un solo lugar las cuatro cosas que hoy fallan:

| Problema de hoy | Cómo lo resuelve |
|---|---|
| Cron que atrasa horas | `pg_cron` corre **dentro de la base**, al minuto. |
| Git como base de datos | Postgres real, con transacciones. Cero commits del bot. |
| Sin identidad, form que no cierra | Login por mail (link mágico, sin contraseña) + **reglas de acceso en la propia base**: cada uno solo puede escribir su voto, y solo si `now() < largada`. El cierre no depende de que un script corra a tiempo: la base rechaza el voto. |
| Ediciones invisibles | Un *trigger* guarda cada cambio de cada voto en una tabla de auditoría. |

**Alternativa evaluada:** Cloudflare (Workers + D1 + Cron Triggers). Igual de
confiable y nunca se pausa, pero hay que escribir a mano el login y las reglas
de acceso. Más código propio = más lugares donde fallar.

**Riesgo a cubrir:** el plan gratuito de Supabase pausa los proyectos sin
actividad durante una semana. En temporada no pasa (hay tráfico y jobs), pero
en el receso sí. Se cubre con un "latido" externo semanal (un workflow de
GitHub o un cron de Cloudflare que consulta la base) y con el chequeo de salud
de abajo. Si en algún momento molesta, el plan pago elimina el problema.

### El modelo de datos

Las tablas principales, y qué bug de 2026 mata cada una:

- **`pilotos`** — id, nombre, número, equipo, temporada. Los votos guardan el
  *id*, no el nombre. **El bug de Hülkenberg deja de ser posible.**
- **`carreras`** — round, nombre en español, largada (UTC), estado. Se llena
  sola desde la API; solo el nombre en español se carga una vez.
- **`votos`** — participante, carrera, categoría, posición, piloto. Con
  restricciones en la base: no se repite un piloto en el top 10, no se vota
  una carrera cerrada, no se vota por otro.
- **`votos_auditoria`** — cada alta, cambio y baja, con hora. **Se acaba el
  "editó la planilla y nadie se enteró".**
- **`resultados`** y **`resultados_revisiones`** — cada vez que la API cambia
  un resultado (penalidad FIA) queda la versión anterior y se recalcula solo.
- **`puntajes`** — una fila por participante × carrera × categoría, con lo
  predicho, lo real, los puntos y el *tipo* de acierto (exacto, a uno, en el
  top 10). **Datos, no texto**: los logros, la pestaña Final y "¿Y si…?" leen
  de acá.
- **`avisos`** — qué se mandó y cuándo. Garantiza que nada se mande dos veces.

### El ciclo de vida de una carrera

Cada carrera pasa sola por estos estados. Un job cada 5 minutos mira el reloj
y la API y la hace avanzar:

```
programada ──► abierta ──► cerrada ──► provisoria ──► final
               (vota)     (largó)     (hay resultado) (48 h sin cambios)
```

- **Abierta:** apenas la anterior queda provisoria (o 7 días antes, lo que
  pase primero). Sale aviso: "ya se puede votar Mónaco".
- **Recordatorios:** 24 h y 1 h antes, **solo a quien todavía no votó**.
- **Cerrada:** a la hora de largada, exacta. Lo hace la base, no un script.
- **Provisoria:** cuando la API trae el resultado (Jolpica; si tarda, OpenF1).
  Se calculan los puntos y sale el aviso con el podio del día.
- **Final:** 48 h sin cambios. Si antes cambió algo (penalidad), se recalcula y
  se avisa qué se movió en la tabla.

Calendario: se importa de la API al empezar la temporada y **se re-sincroniza
todos los días**. Si la FIA cancela o mueve una carrera, el sistema se entera
solo y avisa.

### La página

- Misma estética y misma URL de entrada. Pasa a ser una app (Vite +
  TypeScript) que lee de la base en vivo: el ranking se actualiza solo sin
  recargar.
- **Pestaña "Votar"**: aparece sola cuando hay carrera abierta. Las opciones
  salen de la tabla `pilotos`. Muestra cuenta regresiva hasta el cierre y
  guarda a medida que completás. Podés cambiar el voto hasta la largada.
- **Panel de admin (solo vos):** corregir un resultado, aceptar un voto fuera
  de término, cargar a mano si la API se cae. Todo queda en la auditoría.
  Reemplaza a "editar el Excel".
- Las pestañas de 2026 (ranking, detalle, logros, calendario, perfiles) se
  portan tal cual, más la pestaña Final.

### Avisos

Tres canales, de más a menos recomendable:

1. **Bot de Telegram en un grupo familiar.** API oficial, gratis, sin límites
   prácticos, llega a todos a la vez.
2. **Notificaciones push del navegador.** La página ya es PWA; cada uno acepta
   una vez y recibe en el celular aunque no tenga la página abierta.
3. **WhatsApp.** Si la familia no se muda de WhatsApp, la opción seria es la
   API oficial de WhatsApp Business, que exige verificar un número y plantillas
   aprobadas. CallMeBot puede quedar como respaldo para el admin.

### Que no haya fallos: cómo lo garantizamos

- **Chequeo de salud** cada hora, que te avisa a vos (no a la familia) si:
  terminó una carrera hace más de 6 h y no hay resultado; hay carrera en menos
  de 48 h y la votación no está abierta; un job no corrió en su horario; Jolpica
  y OpenF1 no coinciden en el resultado.
- **Dos fuentes de resultados.** Si no coinciden, el resultado queda retenido y
  te pide confirmar en el panel de admin, en vez de publicar algo dudoso.
- **El motor de puntaje vive en un solo lugar** y se prueba con tests antes de
  cada deploy. Ningún deploy sale con tests en rojo.
- **La prueba de oro:** cargamos toda la temporada 2026 (votos crudos +
  resultados) en el sistema nuevo y el ranking final tiene que salir **idéntico,
  punto por punto**, al de 2026. Ese test queda para siempre.
- **Corrida en sombra:** las últimas carreras de 2026 se calculan en paralelo
  con los dos sistemas y se comparan, antes de apagar el viejo.

---

## Parte 3 — Plan de trabajo

| Cuándo | Qué | Resultado |
|---|---|---|
| **Ahora → noviembre** | Crear el proyecto Supabase. Esquema de tablas y reglas de acceso. Migrar el motor de puntaje para que devuelva datos estructurados. | Base lista, vacía. |
| **Noviembre** | Importar toda la temporada 2026. **Prueba de oro** en verde. Job de calendario y de resultados andando. | El sistema nuevo calcula 2026 igual que el viejo. |
| **Las Vegas → Abu Dhabi** | **Corrida en sombra**: el sistema nuevo trae resultados y calcula solo, sin publicar. Se compara con el viejo. | Confianza real en el reloj y en la API. |
| **Diciembre** | Pestaña Final (se puede hacer ya sobre la base nueva). Cuestionario de mejoras. | Cierre de 2026. |
| **Enero** | Login + pestaña Votar + panel de admin. Reglas 2027 según el cuestionario. **Carrera de prueba** con la familia (una "carrera" inventada para que todos voten una vez y vean que anda). | Votación en la página. |
| **Febrero** | Avisos (Telegram / push). Chequeo de salud. Latido del receso. Importar el calendario 2027 cuando se publique. Votar los tests de pretemporada como ensayo general. | Todo automático. |
| **Marzo — Australia** | Go-live. El Google Form queda **archivado como plan B** la primera carrera, no se borra. | 2027 en piloto automático. |

Los tres archivos de esta carpeta (`AutoForm.js`, `fetch_resultados_2027.py`,
`post_carrera_2027.yml`) quedan reemplazados por este diseño: la base cierra
la votación sola, el job trae resultados al minuto y no hace falta workflow de
publicación. La idea de cada uno sobrevive; el código no hace falta arreglarlo.

---

## Decisiones que necesito de vos para arrancar

1. **Stack:** ¿Supabase (recomendado) o Cloudflare?
2. **Avisos:** ¿la familia se sumaría a un grupo de Telegram, o tiene que ser sí
   o sí WhatsApp?
3. **Login:** ¿link mágico por mail (recomendado: una vez y queda logueado) o
   un link personal que te mando a cada uno por chat?
4. **Repo:** ¿seguimos en `fantasy-f1-2026` o abrimos `fantasy-f1` sin año? Es
   buen momento también para que el repo nuevo arranque **sin los mails** de la
   familia en el historial.
