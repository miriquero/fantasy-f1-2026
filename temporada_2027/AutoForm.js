/**
 * AUTOPILOT PARA GOOGLE FORMS - FANTASY F1 2027
 * 
 * Instalación:
 * 1. Abre tu Google Form de predicciones.
 * 2. Clic en los 3 puntitos arriba a la derecha -> "Editor de secuencias de comandos".
 * 3. Pega este código reemplazando lo que haya.
 * 4. Ejecuta la función "programarCierreDeCarreras()". Te pedirá permisos, acéptalos.
 * ¡Listo! El formulario se cerrará solo en la fecha y hora exacta de cada carrera.
 */

const API_URL = "https://api.jolpi.ca/ergast/f1/2027.json";

function programarCierreDeCarreras() {
  // 1. Borrar triggers anteriores para no duplicar
  const triggers = ScriptApp.getProjectTriggers();
  for (let i = 0; i < triggers.length; i++) {
    ScriptApp.deleteTrigger(triggers[i]);
  }
  
  // 2. Obtener el calendario oficial de F1
  const response = UrlFetchApp.fetch(API_URL);
  const data = JSON.parse(response.getContentText());
  const carreras = data.MRData.RaceTable.Races;
  
  const ahora = new Date();
  
  carreras.forEach(carrera => {
    // La API devuelve fecha y hora en UTC (ej: "2027-03-07" y "13:00:00Z")
    const fechaHoraStr = carrera.date + "T" + carrera.time;
    const fechaCarrera = new Date(fechaHoraStr);
    
    // Solo programar si la carrera es en el futuro
    if (fechaCarrera > ahora) {
      ScriptApp.newTrigger("cerrarFormulario")
        .timeBased()
        .at(fechaCarrera)
        .create();
        
      Logger.log("Cierre programado para " + carrera.raceName + " el " + fechaCarrera);
    }
  });
}

function cerrarFormulario() {
  const form = FormApp.getActiveForm();
  form.setAcceptingResponses(false);
  form.setCustomClosedFormMessage("¡La carrera ha comenzado! Ya no se aceptan más predicciones. ¡Suerte!");
}
