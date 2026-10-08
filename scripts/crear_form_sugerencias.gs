/**
 * crear_form_sugerencias.gs
 * -------------------------
 * Crea el Google Form de sugerencias y mejoras del torneo.
 *
 * Cómo usarlo (una sola vez, tarda 1 minuto):
 *   1. Entrá a https://script.google.com con tu cuenta de Google y tocá
 *      "Nuevo proyecto".
 *   2. Borrá lo que viene escrito y pegá este archivo entero.
 *   3. Arriba elegí la función `crearFormularioSugerencias` y tocá "Ejecutar".
 *   4. La primera vez Google pide permiso para crear formularios en tu
 *      cuenta: aceptá (si dice "app no verificada", entrá en "Configuración
 *      avanzada" → "Ir a ...").
 *   5. Abajo, en el "Registro de ejecución", aparecen dos links: el de editar
 *      (para vos) y el de responder (para mandar al grupo).
 *
 * El formulario queda en tu Google Drive como cualquier otro. Para ver las
 * respuestas en una planilla: pestaña "Respuestas" → "Vincular con Hojas".
 *
 * Las preguntas están escritas sobre las reglas reales del torneo
 * (f1/scoring.py y f1/badges.py): si alguna regla cambia, conviene revisar
 * los textos de la sección 2 antes de volver a correrlo.
 */

function crearFormularioSugerencias() {
  var form = FormApp.create('Fantasy F1 2026 · Buzón de sugerencias 🏎️💨');

  form.setDescription(
    '¡Hola a todos! Ya estamos en la recta final de la temporada y queremos ' +
    'saber qué les gusta, qué no y qué cambiarían del torneo para que el ' +
    'próximo sea todavía más divertido, competitivo y justo.\n\n' +
    'Son 5 secciones cortas (unos 5 minutos). Casi nada es obligatorio: ' +
    'respondé lo que tengas ganas. Si preferís que sea anónimo, dejá el ' +
    'nombre vacío. ¡Sus aportes valen oro!'
  );
  form.setCollectEmail(false);
  form.setProgressBar(true);
  form.setShowLinkToRespondAgain(false);
  form.setConfirmationMessage(
    '¡Gracias! 🏁 Vamos a juntar todas las ideas y las charlamos en el grupo ' +
    'antes de arrancar la próxima temporada.'
  );

  // ---- Sección 1: Vos y el torneo -----------------------------------------

  form.addTextItem()
    .setTitle('Tu nombre o apodo en el torneo')
    .setHelpText('Opcional. Si lo dejás vacío, tu respuesta es anónima.');

  form.addMultipleChoiceItem()
    .setTitle('¿Cómo venís con el torneo este año?')
    .setChoiceValues([
      'Súper enganchado/a: voto todas las carreras y miro el ranking siempre',
      'Bastante: voto casi siempre, aunque a veces se me pasa',
      'Me cuesta seguir el ritmo, pero me divierte estar',
    ])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('Cuando no votaste una carrera, ¿qué pasó?')
    .setHelpText('Podés marcar más de una.')
    .setChoiceValues([
      'Nunca me quedé sin votar',
      'Me olvidé',
      'Me enteré tarde de que había carrera',
      'El horario de la carrera (de madrugada, etc.)',
      'No sabía bien a quién poner, así que no voté',
      'El formulario de votación es largo o incómodo',
    ])
    .showOtherOption(true);

  // ---- Sección 2: Puntaje y reglas ----------------------------------------

  form.addPageBreakItem()
    .setTitle('Puntaje y reglas')
    .setHelpText(
      'Así se puntúa hoy cada piloto del top 10 que predecís:\n' +
      '• Posición exacta: 10 pts\n' +
      '• Errarle por un puesto: 5 pts\n' +
      '• Acertar que entraba al top 10 pero en otro lugar: 1 pt\n' +
      'Además: vuelta rápida exacta = 10 pts, y la posición de Colapinto ' +
      '= 10 pts exacta o 5 pts por un puesto.'
    );

  form.addScaleItem()
    .setTitle('¿Qué te parece el sistema de puntos actual?')
    .setBounds(1, 5)
    .setLabels('Muy injusto / aburrido', 'Excelente, justo y dinámico')
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Sobre los puntos por posición del top 10…')
    .setChoiceValues([
      'Está bien como está',
      'Errarle por 2 puestos también debería sumar algo',
      'Acertar el ganador (P1) debería valer más que acertar el P10',
      'La posición exacta debería valer todavía más',
      'Acertar que entraba al top 10 debería valer más que 1 punto',
    ])
    .showOtherOption(true);

  form.addMultipleChoiceItem()
    .setTitle('La vuelta rápida (10 pts si la acertás)…')
    .setChoiceValues([
      'Dejarla como está',
      'Que valga menos (por ejemplo 5 pts)',
      'Sacarla',
      'Reemplazarla por otra pregunta (contanos cuál al final)',
    ]);

  form.addMultipleChoiceItem()
    .setTitle('La predicción de Colapinto…')
    .setChoiceValues([
      'Dejarla como está',
      'Que cada uno elija "su" piloto para predecir la posición',
      'Sumar otro piloto además de Franco',
      'Sacarla',
    ])
    .showOtherOption(true);

  form.addCheckboxItem()
    .setTitle('¿Qué preguntas extra te gustaría sumar a la votación de cada carrera?')
    .setHelpText('Marcá todas las que te copen (o ninguna).')
    .setChoiceValues([
      'Quién hace la pole',
      'Piloto del día (Driver of the Day)',
      'Primer abandono de la carrera',
      '¿Sale el safety car? (sí / no)',
      'Qué equipo suma más puntos en la carrera',
      'Quién remonta más posiciones',
      'Comodín x2: una vez por temporada duplicás los puntos de una carrera',
      'Ninguna, prefiero que la votación siga corta',
    ])
    .showOtherOption(true);

  form.addParagraphTextItem()
    .setTitle('¿Alguna otra regla que sumarías, cambiarías o sacarías?');

  // ---- Sección 3: Formato del torneo --------------------------------------

  form.addPageBreakItem()
    .setTitle('Formato del torneo');

  form.addMultipleChoiceItem()
    .setTitle('¿Hasta cuándo debería poder votarse cada carrera?')
    .setChoiceValues([
      'Hasta la largada, como ahora',
      'Hasta antes de la clasificación (sin saber la grilla)',
      'Hasta el viernes, antes de las prácticas',
    ])
    .showOtherOption(true);

  form.addMultipleChoiceItem()
    .setTitle('Si alguien no vota una carrera, ¿qué debería pasar?')
    .setChoiceValues([
      'Suma 0, como ahora',
      'Se le copia automáticamente su voto de la carrera anterior',
      'Se le asigna el puntaje más bajo de esa carrera',
      'Suma 0 y además resta algunos puntos',
    ])
    .showOtherOption(true);

  form.addMultipleChoiceItem()
    .setTitle('¿Sumamos las carreras Sprint?')
    .setChoiceValues([
      'No, solo los Grandes Premios',
      'Sí, sumando al mismo ranking (con menos puntos)',
      'Sí, pero como un torneo aparte',
    ]);

  form.addCheckboxItem()
    .setTitle('¿Sumarías mini-torneos dentro de la temporada?')
    .setHelpText('Podés marcar más de una.')
    .setChoiceValues([
      'No, un único torneo de punta a punta',
      'Dividir el año en Apertura y Clausura',
      'Una "Copa playoff" en las últimas carreras',
      'Un mini-torneo por continente / gira',
      'Duelos mano a mano (cada carrera te toca un rival del grupo)',
    ])
    .showOtherOption(true);

  form.addParagraphTextItem()
    .setTitle('Premios y castigos: ¿qué le darías al campeón y qué "prenda" para el último?')
    .setHelpText('Trofeo, asado pagado, foto de perfil obligatoria por una semana… lo que se te ocurra.');

  // ---- Sección 4: La página, los logros y los avisos ----------------------

  form.addPageBreakItem()
    .setTitle('La página, los logros y los avisos');

  form.addScaleItem()
    .setTitle('¿Qué tan clara te resulta la página del ranking?')
    .setBounds(1, 5)
    .setLabels('Un chino, no entiendo nada', 'Súper clara');

  form.addCheckboxItem()
    .setTitle('¿Qué es lo que más mirás de la página?')
    .setChoiceValues([
      'El ranking general',
      'El detalle de puntos de cada carrera',
      'Los gráficos de evolución',
      'Los logros (badges)',
      'Los perfiles y el Hall of Fame',
      'El calendario',
      'Casi no la miro',
    ]);

  form.addMultipleChoiceItem()
    .setTitle('Los logros (Francotirador, Oráculo, Hincha de Franco, etc.)…')
    .setChoiceValues([
      'Me encantan, quiero más',
      'Están bien como están',
      'Son demasiado difíciles, casi nadie los saca',
      'No les doy mucha bola',
    ]);

  form.addParagraphTextItem()
    .setTitle('¿Se te ocurre un logro nuevo?')
    .setHelpText('Nombre, emoji y qué hay que hacer para ganarlo. Ej.: "🐢 Tortuga: votar en el último minuto 5 veces".');

  form.addMultipleChoiceItem()
    .setTitle('Los avisos de WhatsApp (recordatorio para votar y aviso del ranking nuevo)…')
    .setChoiceValues([
      'Están perfectos',
      'Quiero más recordatorios antes de la carrera',
      'Son demasiados',
      'Ni me enteré de que existían',
    ])
    .showOtherOption(true);

  form.addScaleItem()
    .setTitle('¿Qué tan cómodo te resulta el formulario de votación de cada carrera?')
    .setBounds(1, 5)
    .setLabels('Un sufrimiento', 'Facilísimo');

  // ---- Sección 5: Cierre --------------------------------------------------

  form.addPageBreakItem()
    .setTitle('Cierre');

  form.addParagraphTextItem()
    .setTitle('Cualquier otra idea loca, queja o reclamo formal que no hayamos preguntado');

  form.addMultipleChoiceItem()
    .setTitle('¿Te prendés para la temporada 2027?')
    .setChoiceValues([
      '¡Obvio! Y traigo a alguien más',
      'Sí, de una',
      'Capaz, depende de los cambios',
      'Creo que esta vez paso',
    ])
    .setRequired(true);

  // Los formularios nuevos de Google arrancan sin publicar; esto lo deja
  // abierto para recibir respuestas. Si la versión de Apps Script todavía no
  // tiene setPublished, se publica a mano con el botón "Publicar".
  if (typeof form.setPublished === 'function') {
    form.setPublished(true);
  }
  form.setAcceptingResponses(true);

  Logger.log('✏️  Editar el formulario:   ' + form.getEditUrl());
  Logger.log('📨 Link para el grupo:     ' + form.getPublishedUrl());
}
