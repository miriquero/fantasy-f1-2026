# Torneo de Fórmula 1 familiar — contexto completo del proyecto

**Para el agente de código que va a trabajar en esto.** Leé todo antes de tocar
un archivo. La sección 6 ("Reglas duras") no es opcional: cada punto está ahí
porque ya falló en producción.

---

## 1. Qué es este proyecto

Un torneo de predicciones de Fórmula 1 que juega una familia de 10 personas,
en la temporada 2026. No es un fantasy de armar equipos: **no hay escuderías,
ni presupuesto, ni mercado de pases**. Antes de cada carrera cada participante
predice el resultado, y después de la carrera el sistema reparte puntos.

El sistema entero existe para que nadie tenga que hacer nada a mano. Funciona
solo: junta los votos, busca el resultado oficial, calcula los puntos, publica
una página web y avisa por WhatsApp.

- **Repositorio:** `miriquero/fantasy-f1-2026` — **es público**
- **Página publicada:** https://miriquero.github.io/fantasy-f1-2026/ranking_f1.html
- **Rama de trabajo:** `master`, directo, sin pull requests
- **Lenguaje:** Python 3.11 (es la versión de CI; en la máquina local hay 3.14)

### Qué se predice en cada carrera

12 campos:

1. a 10. Los **diez primeros puestos**, en orden, eligiendo un piloto para cada
   posición.
11. Quién hace la **vuelta rápida**.
12. En qué puesto termina **Franco Colapinto** (es una categoría aparte porque
    es el piloto argentino y a la familia le interesa particularmente).

### Las reglas de puntaje, exactas

Para cada uno de los diez puestos predichos:

| Situación | Puntos |
|---|---|
| El piloto terminó exactamente en el puesto que le pusiste | **10** |
| Le erraste por un solo puesto | **5** |
| El piloto terminó en el top 10 pero le erraste la posición por 2 o más | **1** |
| El piloto terminó 11º o peor, o no terminó la carrera | **0** |

**Regla de borde, importante:** el top 10 es un corte duro. Si pusiste a un
piloto 10º y terminó 11º, eso **no** es "errarle por uno": es **0 puntos**.
Abajo del top 10 no hay nada, ni el punto de consuelo ni la diferencia de uno.
Esto fue una decisión explícita del dueño del torneo y está fijada en los tests
(`tests/test_scoring.py::test_el_que_termina_p11_no_paga_nada`). **No la
cambies.**

Aparte:

| Categoría | Puntos |
|---|---|
| Vuelta rápida acertada | **10** |
| Colapinto en el puesto exacto | **10** |
| Colapinto errado por un puesto | **5** |
| Colapinto errado por más, o no terminó | **0** |

Colapinto **no** tiene la restricción del top 10: su posición puede ser
cualquiera de la grilla (en Singapur 2026 terminó P21 y eso es válido).

Máximo teórico por carrera: 10 × 10 + 10 + 10 = **120 puntos**.

### Los 15 logros

Hay un sistema de medallas que se calcula solo. Están todos auditados uno por
uno y la lógica es correcta:

`Francotirador`, `Racha Caliente`, `Hincha de Franco`, `Bomba de Puntos`,
`Adivino`, `Muralla`, `Remontada Épica`, `Estratega`, `Consistente`,
`Apostador Nato`, `Marea Alta`, `Arquitecto`, `Oráculo`, `Perfeccionista`,
`Rey de la Temporada`.

---

## 2. Por qué existe este documento y quién lo va a usar

El trabajo que queda para la temporada 2027 es largo, iterativo y en buena
parte mecánico: hay que construir una sección nueva de la página, arreglar tres
archivos que están a medio hacer, y aplicar un conjunto de cambios de reglas
que todavía no están decididos.

El dueño del proyecto va a hacer ese trabajo con **un agente de código abierto
que corre localmente** (del estilo de OpenCode), en vez de seguir en la
herramienta donde se hizo 2026. Las razones son prácticas: el trabajo es
extenso y conviene no depender de límites de uso externos, todo el repositorio
está en su máquina, y un agente local puede iterar sobre los tests sin
fricción.

**Lo que eso significa para vos, agente que recibe esto:** no vas a tener el
historial de las conversaciones donde se encontró cada cosa. Este documento es
ese historial comprimido. Todo lo que está acá se descubrió rompiendo algo
primero.

Hay dos documentos más en el repositorio que son tus compañeros de este:

- **`temporada_2027/PLAN_2027.md`** — el plan de trabajo priorizado, con la
  revisión de los tres archivos a medio hacer.
- **`cuestionario_mejoras.md`** — el cuestionario que se le va a mandar a la
  familia.

---

## 3. Cómo funciona hoy

### El circuito completo

```
  Google Form  (la familia vota antes de cada carrera)
        │
        ▼
  Google Sheets  (una fila por voto, con marca temporal)
        │
        │   fetch_votos.py   ← lee la planilla con credenciales de servicio
        ▼
  respuestas/respuestas_<carrera>.csv   (uno por carrera, en el repo)
        │
        │                    API de Jolpica (Ergast) ──┐
        │                                              │
        │   fetch_resultados.py  ← empareja POR FECHA ─┘
        ▼
  resultados.json   (top 11, vuelta rápida y puesto de Colapinto por carrera)
        │
        │   fantasy_f1.py  →  f1/main.py  (orquesta todo el pipeline)
        ▼
  ranking_f1.html   (una sola página, autocontenida, se commitea al repo)
        │
        ▼
  GitHub Pages  (publica el HTML del repositorio)
        │
        ▼
  notificar.py  →  WhatsApp vía CallMeBot  (avisa a la familia)
```

### Los pasos, uno por uno

**`fetch_votos.py`** se conecta a Google Sheets con una cuenta de servicio y
parte la planilla en un CSV por carrera. Resuelve tres cosas por su cuenta:
descarta votos duplicados quedándose con el más reciente, ignora los que
llegaron después de la largada, y deja un aviso si el formulario manda el
nombre de una carrera que el calendario no conoce.

**`fetch_resultados.py`** baja el resultado oficial. Lo importante: **empareja
cada carrera del torneo con su número de round de la API comparando fechas**,
no por un número escrito a mano. Eso es así porque la FIA insertó el GP de
Bahréin (mudado a Sepang, Malasia) como round 16 a mitad de temporada y corrió
toda la numeración posterior. Con rounds escritos a mano, el sistema habría
pedido el round 16 y guardado la carrera equivocada. También detecta cuando la
FIA corrige un resultado después (penalidades) y deja un aviso.

**`fantasy_f1.py`** es un envoltorio de 15 líneas que llama a `f1.main`. Ese
módulo valida `resultados.json`, calcula todo y escribe el HTML.

**`notificar.py`** manda los mensajes de WhatsApp. Recibe un tipo (`exito`,
`error`, `recordatorio`, `ultima_hora`, `tardios`, `penalidad`,
`carrera_desconocida`) y un texto.

### La arquitectura del paquete `f1/`

El proyecto empezó como un único archivo de 3234 líneas y se partió en módulos
por responsabilidad. El corte se hizo verificando que el HTML generado quedara
**byte por byte idéntico** antes y después.

| Módulo | Líneas | De qué se ocupa |
|---|---|---|
| `config.py` | 81 | Lista de pilotos, calendario de las 23 carreras, rutas, mapa de países |
| `normalizacion.py` | 153 | Traduce cualquier grafía de piloto o carrera al nombre canónico |
| `participantes.py` | 75 | Mapea mail → apodo, sin que el mail llegue nunca al HTML |
| `consola.py` | 18 | Colores de la salida por terminal |
| `paleta.py` | 104 | Color de cada participante, validado para daltonismo |
| `calendario.py` | 207 | Orden cronológico, banderas SVG y trazado de cada circuito |
| `scoring.py` | 281 | **La regla de puntaje** y los lectores del texto de detalle |
| `badges.py` | 524 | Los 15 logros |
| `graficos.py` | 238 | Gráficos SVG en vivo (barras, evolución, sparklines) |
| `perfiles.py` | 275 | Panel individual por participante, Hall of Fame, estadísticas |
| `validacion.py` | 122 | Valida `resultados.json` antes de calcular |
| `analisis.py` | 193 | Proyección al título (quién sigue vivo) y cara a cara |
| `avisos.py` | 57 | Escribe los avisos que después levanta el workflow |
| `render.py` | 204 | Arma el HTML final con Jinja2 |
| `main.py` | 135 | Orquesta el pipeline completo |

Las plantillas están en `f1/templates/`: `ranking.html.j2` (54 KB), más CSS y
JS de animaciones, y `sprite.svg` (59 KB) con 21 banderas y 24 trazados de
circuito embebidos.

### La página

Una sola página autocontenida, oscura, con identidad visual de F1, pensada
primero para el teléfono. Es una PWA (`manifest.json` + `sw.js`). Tiene seis
pestañas: **Acumulado**, **Carreras**, **Calendario**, **Logros**, **Perfiles**
y **Más**.

### Las automatizaciones (3 workflows de GitHub Actions)

**`post_carrera.yml`** — el que calcula y publica.
Corre domingos y lunes a las 13:00 y 22:00 UTC. Hace el circuito completo:
votos, resultados, los tres avisos, genera el HTML, commitea y avisa.

**`recordatorio.yml`** — avisa a quienes no votaron todavía.
Corre **cada hora** y el script decide si corresponde mandar algo. Tiene un
diseño de dos ventanas que vale la pena entender:

```python
VENTANA_ANCHA  = 20 * 60   # asegura la entrega
VENTANA_ULTIMA =  2 * 60   # extra si una corrida cae cerca de la largada
```

Existe porque **GitHub no garantiza los crons programados**. Se midió sobre el
historial real de este repositorio: de los crons horarios solo se ejecutó el
23%. Con una sola ventana angosta el recordatorio no llegaba. Con la ventana
ancha de 20 horas, las 412 ventanas históricas contenían al menos una corrida.

**`ci.yml`** — corre los tests en cada push a `master` y en cada pull request.

### Los tests

**216 tests en 15 archivos** (1344 líneas). Correr con:

```bash
python -m pytest -q
```

Hay un `pytest.ini` que define `pythonpath = .` y `testpaths = tests`. Existe
porque `pytest` y `python -m pytest` no resuelven igual el `sys.path`: sin ese
archivo, CI fallaba con `ModuleNotFoundError: No module named 'f1'` aunque en
local pasara todo.

Tests que conviene conocer antes de tocar nada:

- **`test_render_smoke.py`** — genera la página y verifica que **no haya ni un
  mail** en el HTML. Es la última defensa de la privacidad de la familia.
- **`test_lectura_detalle.py`** — ata los lectores de los logros al texto que
  escribe el cálculo, sobre datos generados de verdad.
- **`test_nombres_votos.py`** — que una grafía del formulario encuentre al
  mismo piloto del resultado.
- **`test_validacion.py`** — que el validador no rechace un resultado real.
- **`test_recordatorio.py`** — la lógica de las dos ventanas.

---

## 4. Estado actual, con números

Al 11 de octubre de 2026:

- **17 de 23 carreras** jugadas. Quedan 6. La última es **Abu Dhabi, el 6 de
  diciembre de 2026**.
- **10 participantes.** El líder tiene 722 puntos; el segundo, 650.
- **142 votos emitidos de 170 posibles.** Falta el 16%, y no está repartido:
  dos personas se perdieron 11 y 8 carreras respectivamente, y por eso están
  últimas — no porque predigan mal.
- **216 tests, CI en verde.**

---

## 5. Cómo va a funcionar después

La forma general está decidida; los detalles dependen del cuestionario (ver
sección 7). El plan completo y priorizado está en
**`temporada_2027/PLAN_2027.md`**. El resumen:

### Lo que se agrega

**Una pestaña "Final"**, que es la pieza más grande que falta. Dos partes:

- Un **podio ceremonial** para los tres primeros: los escalones suben en orden
  3º, 2º, 1º, con el color de cada uno y confeti en el color del campeón. Cada
  escalón se abre y muestra puntos, carreras ganadas, logros y mejor carrera.
- Una **tarjeta de temporada por participante**, formato tipo Wrapped: tu
  piloto fetiche, el que más te traicionó, tu mejor y peor carrera, aciertos
  exactos contra el promedio familiar, tu némesis en el mano a mano.
  Exportable como imagen para compartir.

Dato que importa para implementarla: **todas las predicciones crudas están
archivadas** en `respuestas/`, 142 filas hoy y unas 210 al cerrar. No hace
falta guardar nada nuevo.

Requisito de diseño: la pestaña **se desbloquea sola** cuando se puntúa la
última carrera. Hasta entonces muestra una cuenta regresiva y quién sigue vivo
matemáticamente (ese cálculo ya existe en `analisis.py`). El dueño no quiere
tener que activar nada a mano.

Además: **récords de la temporada** y un panel **"¿Y si...?"** donde se apagan
y prenden carreras y la tabla se reordena en vivo.

### Lo que se automatiza más

Tres archivos a medio hacer en `temporada_2027/` apuntan a: cerrar el
formulario solo a la hora de largada, traer resultados con FastF1 en minutos
en vez de horas, y un workflow más denso.

**Las tres ideas son correctas. Ninguno de los tres archivos funciona como
está, y dos tienen fallas que matarían el torneo.** La revisión detallada está
en `PLAN_2027.md`, sección 5. Léela antes de adoptar cualquiera de los tres.

### Lo que se endurece

Siete problemas estructurales, todos con un incidente real detrás: los nombres
del formulario, las cotas escritas a mano, que los commits del bot no disparen
CI, que editar la planilla después de la carrera sea invisible, el
acoplamiento de los logros al texto, la densidad del cron, y el calendario
escrito a mano.

---

## 6. Reglas duras

**Cada una de estas está acá porque ya falló.** No son preferencias de estilo.

### 6.1 El repositorio es público

- **Nunca** commitees `participantes.json` ni
  `fantasy-f1-500915-613a0c111715.json`. El primero mapea los mails de la
  familia a sus apodos; el segundo son las credenciales de Google. Los dos
  están en `.gitignore` y tienen que seguir estándolo.
- **Ningún mail puede aparecer en el HTML ni en los CSV.** Hay un test que lo
  verifica. Si lo rompés, lo estás publicando en internet.
- En producción los apodos llegan por el secret `PARTICIPANTES_JSON`. Si ese
  secret falta, el sistema muestra la parte del mail antes del `@` — nunca el
  mail completo.

### 6.2 No reescribas el historial publicado

El repositorio es el registro de un torneo con diez personas que dependen de
él. No hagas `rebase`, `squash` ni `force-push` sobre commits que ya están en
`origin/master`. Si hay que corregir algo, se corrige con un commit nuevo
encima.

### 6.3 El HTML generado se commitea

`ranking_f1.html` es el sitio publicado: GitHub Pages lo sirve directo del
repositorio. No lo pongas en `.gitignore` ni lo trates como artefacto
descartable. Si cambiás código que afecta el render, regeneralo y commiteá el
resultado.

### 6.4 Los logros leen el texto que escribe el cálculo

Los 15 logros se enteran de qué acertó cada uno **parseando las cadenas de
texto** que arma `calcular_puntos_y_detalles()`. Es un acoplamiento frágil y ya
rompió tres cosas sin que fallara nada visible:

1. Reformatear `"Colapinto: EXACTO"` a `"Colapinto: Exacto en P9"` dejó el
   logro "Hincha de Franco" **inalcanzable para siempre**.
2. Esa misma línea empezó a contarse como acierto de posición de un piloto,
   porque contiene `"Exacto en P9"`, inflando otros dos logros.
3. Buscar `"Exacto en P1"` con `in` también matchea `"Exacto en P10"`, así que
   los aciertos del décimo puesto se contaban como aciertos del ganador.

Los tres daban resultados plausibles. Nadie se enteró hasta que alguien miró la
tabla y le pareció raro.

**Si cambiás la redacción de una línea de detalle, tenés que actualizar los
lectores en `scoring.py` en el mismo commit.** Viven al lado del escritor
justamente para que no se separen, y `test_lectura_detalle.py` los ata sobre
datos generados. La refactorización correcta —que el cálculo devuelva datos
estructurados y el texto se arme aparte— está pendiente y es la más valiosa.

### 6.5 Ningún número que describa la realidad va escrito a mano

El validador tenía la posición máxima fija en `20`, que era el tamaño de grilla
de temporadas anteriores. En 2026 corren 11 equipos: en Singapur clasificaron
22 autos, Colapinto terminó P21, y el validador **rechazó la carrera entera**.
No puntuó nadie, y el motivo no se veía desde ningún otro lado.

Ahora la cota sale de `len(PILOTOS)`. Hacé lo mismo con cualquier cota nueva:
cantidad de autos, de carreras, de participantes.

### 6.6 Normalizá las dos puntas de cualquier comparación de nombres

El bug más caro de 2026. El formulario ofrecía `Nico Hülkenberg` con diéresis y
`Olie Bearman` con una sola L; la lista del torneo escribe `Nico Hulkenberg` y
`Ollie Bearman`. El resultado de la API se normalizaba, el voto no, y el cruce
fallaba en silencio: el sistema contestaba "no entró al top 10", que es una
respuesta perfectamente plausible.

**16 predicciones mal puntuadas en 8 carreras, sobre 9 de los 10
participantes.** Incluido un acierto exacto de 10 puntos contado como cero.

`calcular_puntos_y_detalles()` ahora normaliza el piloto predicho, las claves
del resultado y la vuelta rápida, sin confiar en que quien la llame lo haya
hecho. Mantené esa propiedad.

### 6.7 Los commits del bot no disparan CI

GitHub no reencadena workflows hechos con `GITHUB_TOKEN`. Consecuencia real:
**CI estuvo en rojo una semana entera** (del 4 al 11 de octubre de 2026) sin
que nadie se enterara, porque un commit cambió la regla de puntaje y dejó dos
tests afirmando la anterior.

Mientras eso no se arregle, **el bot puede publicar puntos con el código
roto**. Corré los tests vos antes de pushear, siempre.

### 6.8 No uses heredocs de bash para contenido con secuencias de escape

En este proyecto la expansión de `\n` dentro de heredocs corrompió archivos
**cuatro veces**, y una llegó a producción. Usá herramientas de escritura de
archivos, o scripts de Python con reemplazos exactos verificados con `assert`.

### 6.9 Finales de línea

Hay un `.gitattributes` con `* text=auto eol=lf`. Vas a ver advertencias de
`CRLF will be replaced by LF` al commitear desde Windows: son normales y no
hay que hacer nada. No las "arregles" cambiando la configuración.

### 6.10 Lo que no decide un agente

Las reglas del torneo las decide el dueño, no vos. Si encontrás una
inconsistencia entre lo que un logro promete y lo que hace, **reportala; no la
resuelvas por tu cuenta**. Hay dos identificadas y deliberadamente sin tocar:

- **"Rey de la Temporada"** dice *"al cierre de la temporada"* pero se le
  otorga a quien va primero hoy.
- **"Consistente"** mide la mitad de arriba contra los 10 inscriptos, cuando en
  la mayoría de las carreras votaron 7 u 8.

---

## 7. El cuestionario: cómo se deciden los cambios

Los cambios de reglas para 2027 **no se van a decidir por intuición**. Hay un
cuestionario escrito y listo en **`cuestionario_mejoras.md`**: 16 preguntas,
con el tipo de campo de Google Forms anotado en cada una, pensado para
completarse en unos cinco minutos.

Se le va a mandar a los 10 participantes antes de diciembre, mientras la
temporada está fresca. Pregunta por cosas concretas del torneo real, no
genéricas: qué opinan del sistema de puntos, si entendían la regla del corte en
el top 10, por qué dejaron de votar cuando dejaron de votar, si el recordatorio
les sirve, si los logros les parecen inalcanzables, y qué premio o cargada
quieren para el cierre.

**Cómo usarlo como agente:** varias de las decisiones pendientes están
explícitamente delegadas a preguntas de ese formulario. En `PLAN_2027.md` cada
decisión dice qué pregunta la resuelve. Cuando lleguen las respuestas, el dueño
va a traducirlas en instrucciones concretas. **No implementes cambios de reglas
antes de eso**, ni asumas un resultado: el punto del cuestionario es que la
familia decida.

Las preguntas que más peso tienen sobre el código:

- **P2, P3, P8** — participación: qué hacer con quien falta a muchas carreras.
  Opciones en juego: descartar la peor carrera de cada uno, exigir un mínimo de
  carreras para la tabla general, o no cambiar nada.
- **P5, P6** — si la regla del corte en el top 10 se entiende y se considera
  justa.
- **P9** — si el recordatorio tiene que llegar antes, o dos veces.
- **P11, P12** — umbrales de los logros, y si "Rey de la Temporada" debería
  esperar al final.
- **P15** — si les interesa la pestaña Final antes de construirla.

---

## 8. Cómo empezar

### Preparar el entorno

```bash
pip install -r requirements-dev.txt
```

Dependencias: `pandas`, `numpy`, `Jinja2`, `google-auth`,
`google-auth-httplib2`, `google-api-python-client`, y `pytest` para los tests.

### Verificar que todo está sano

```bash
python -m pytest -q
```

Tienen que pasar 216. Si ves fallas en `test_scripts.py` referidas a
`scratch_p10_p11.py` o `show_ranking.py`, son dos archivos sueltos en la raíz
con BOM que no están en el repositorio: no llegan a CI y se pueden borrar.

### Regenerar la página sin tocar nada externo

```bash
python fantasy_f1.py
```

Lee `respuestas/` y `resultados.json`, que ya están en el repositorio, y
reescribe `ranking_f1.html`. No necesita credenciales ni red.

### Lo que NO deberías correr sin motivo

- `fetch_votos.py` — necesita las credenciales de Google y toca la planilla de
  la familia.
- `notificar.py` — **manda WhatsApp de verdad** a la familia.
- Cualquier `git push` — publica en el sitio que los diez miran.

### Orden de trabajo sugerido

Está en `temporada_2027/PLAN_2027.md`, sección 6. Lo primero y más barato: que
el workflow corra los tests antes de publicar, porque hoy el bot puede publicar
puntos con el código roto.

---

## 9. Resumen de los tres documentos

| Archivo | Para qué |
|---|---|
| **`CONTEXTO_PARA_LA_IA.md`** (este) | Cómo funciona todo y qué no se puede romper |
| **`temporada_2027/PLAN_2027.md`** | El plan priorizado y la revisión de los archivos a medio hacer |
| **`cuestionario_mejoras.md`** | El cuestionario que define las decisiones de reglas |
