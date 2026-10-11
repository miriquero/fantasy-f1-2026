# Preparativos para la Temporada 2027 (Autopilot)

He dejado todos los archivos necesarios para automatizar al 100% el torneo de 2027 en esta carpeta. Para que la actual temporada siga funcionando sin problemas, no he reemplazado tus archivos en la raíz, sino que los dejé aquí listos para cuando quieras hacer el "cambio de llantas".

## 1. El cierre automático del Formulario
Abre el archivo `AutoForm.js` que dejé en esta carpeta.
- Pégalo en el **Editor de Secuencias de Comandos** de tu Google Form.
- Dale "Ejecutar" a la función principal una sola vez en febrero de 2027.
- **Resultado:** El formulario leerá a qué hora es cada carrera del año y se bloqueará solo para no recibir más respuestas exactamente a la hora de largada. Ya no tendrás que acordarte de cerrarlo.

## 2. La velocidad de resultados (FastF1)
El archivo `fetch_resultados_2027.py` es el reemplazo de tu actual buscador de resultados.
- Elimina a Jolpica de la ecuación.
- Usa la librería oficial y en vivo (`pip install fastf1`).
- En lugar de esperar 12 horas o al lunes para calcular los puntos, tu torneo se va a actualizar minutos después del podio.

## 3. Acción Inteligente en GitHub
El archivo `post_carrera_2027.yml` reemplaza al que tienes en `.github/workflows/`.
- Ya no se ejecuta solo una vez al día.
- Revisará automáticamente el estado de la API los fines de semana y correrá todo el cálculo sin intervención humana.

Cuando termine la temporada en diciembre, simplemente reemplaza los archivos viejos por estos, ¡y disfruta tu 2027 sin trabajar gratis!
