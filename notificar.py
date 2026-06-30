"""
notificar.py
------------
Envia notificaciones por WhatsApp via CallMeBot.

Uso:
    python notificar.py exito "URL del ranking"
    python notificar.py error "mensaje de error"

Variables de entorno requeridas:
    CALLMEBOT_PHONE   -> tu numero con codigo de pais, sin + ni espacios (ej: 5492616994813)
    CALLMEBOT_APIKEY  -> tu apikey de CallMeBot
"""

import os
import sys
import urllib.request
import urllib.parse

def enviar_whatsapp(mensaje):
    phone  = os.environ.get("CALLMEBOT_PHONE")
    apikey = os.environ.get("CALLMEBOT_APIKEY")

    if not phone or not apikey:
        print("ERROR: faltan CALLMEBOT_PHONE o CALLMEBOT_APIKEY como variables de entorno.")
        return False

    texto_codificado = urllib.parse.quote(mensaje)
    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={texto_codificado}&apikey={apikey}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FantasyF1/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            resultado = resp.read().decode("utf-8")
            print(f"Notificacion enviada. Respuesta: {resultado[:200]}")
            return True
    except Exception as e:
        print(f"ERROR al enviar notificacion: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Uso: python notificar.py [exito|error] [mensaje opcional]")
        sys.exit(1)

    tipo = sys.argv[1]
    extra = sys.argv[2] if len(sys.argv) > 2 else ""

    if tipo == "exito":
        mensaje = (
            "Fantasy F1 actualizado!\n\n"
            "El ranking de la ultima carrera ya esta listo.\n\n"
            f"{extra}\n\n"
            "Reenvia este mensaje al grupo de la familia"
        )
    elif tipo == "error":
        mensaje = (
            "Fantasy F1 - Error en la actualizacion\n\n"
            "El workflow automatico fallo y el ranking NO se actualizo.\n\n"
            f"Detalle: {extra}\n\n"
            "Revisa GitHub Actions para mas info."
        )
    else:
        print(f"Tipo desconocido: {tipo}. Usar 'exito' o 'error'.")
        sys.exit(1)

    ok = enviar_whatsapp(mensaje)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
