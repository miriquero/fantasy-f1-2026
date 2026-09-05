# -*- coding: utf-8 -*-
"""Colores del sitio: paleta categorica validada y asignacion por persona.

Por que este archivo existe
---------------------------
La paleta vieja eran 8 neones elegidos a ojo (`#39FF14`, `#FF69B4`...). Pasada
por el validador contra el fondo oscuro real, 7 de los 8 quedaban fuera de la
banda de luminosidad y la separacion para daltonismo raspaba el piso: colores
que brillan mucho pero que no se distinguen entre si, que es exactamente lo
contrario de lo que tiene que hacer una paleta categorica.

Peor: el color se asignaba por POSICION en la tabla. Si dos personas se pasaban
en el ranking, se intercambiaban los colores; y como el panel de logros usaba
otro orden, la misma persona tenia un color distinto en cada panel.

Las dos cosas estan arregladas aca.

Cuantos colores se pueden usar de verdad
----------------------------------------
Se probaron paletas generadas de 10, 9, 8, 7 y 6 tonos equiespaciados: ninguna
paso. Con la misma luminosidad en todos los slots, la deuteranopia colapsa el
eje rojo-verde y el violeta y el azul quedan a ΔE 0.9, o sea identicos. Lo que
hace funcionar a una paleta categorica no es separar los tonos: es que la
luminosidad varie entre slots.

Por eso estos 8 valores no se inventaron: salen de la paleta de referencia del
skill de visualizacion, que si varia la luminosidad, y estan verificados contra
la superficie real de las tarjetas del sitio:

    node validate_palette.js \\
        "#3987e5,#d95926,#199e70,#c98500,#d55181,#008300,#9085e9,#e66767" \\
        --mode dark --surface "#111111"
    -> ALL CHECKS PASS  (banda de luminosidad, piso de croma, separacion
       deutan/protan/tritan, piso de vision normal, contraste >= 3:1)

NO reordenar ni reemplazar estos valores a ojo. Cualquier cambio hay que volver
a pasarlo por ese script.

Y son 8 para 10 participantes a proposito: no existe una paleta de 10 que se
distinga de forma confiable. Por eso el color NUNCA identifica solo. En las
fichas siempre va con el nombre y las iniciales al lado, y en los graficos no
se pintan diez series de colores: se resalta una sobre un fondo neutro.
"""

from .participantes import cargar_apodos

# Orden fijo. El slot 0 es siempre el primero asignado, nunca se cicla al azar.
CATEGORICOS = [
    "#3987e5",   # azul
    "#d95926",   # naranja
    "#199e70",   # aqua
    "#c98500",   # amarillo
    "#d55181",   # magenta
    "#008300",   # verde
    "#9085e9",   # violeta
    "#e66767",   # rojo claro
]

# Rojo de marca. Reservado para acentos de la interfaz (la barra activa, el
# proximo evento). NO se usa como color de participante: si fuera las dos
# cosas, no se sabria si el rojo significa "esta persona" o "prestá atencion".
ROJO_MARCA = "#E10600"

# Tinta de los graficos sobre fondo oscuro.
INK_PRIMARIO = "#f0f0f0"
INK_SECUNDARIO = "#c3c2b7"
INK_MUTED = "#898781"
GRILLA = "#2c2c2a"
EJE = "#383835"

# Podio.
ORO, PLATA, BRONCE = "#FFD700", "#C0C0C0", "#CD7F32"


def _roster():
    """Todos los apodos del torneo, ordenados. Fuente: participantes.json."""
    return sorted(set(cargar_apodos().values()))


def color_participante(nombre: str) -> str:
    """Color fijo de una persona, el mismo en toda la pagina y toda la temporada.

    Se indexa por el orden alfabetico del plantel, no por la posicion en la
    tabla: asi el color pertenece a la persona y no cambia cuando alguien la
    pasa en el ranking.

    Si el plantel no esta disponible (por ejemplo en CI, sin participantes.json)
    se cae a un indice derivado del propio nombre, que tambien es estable.
    """
    if not nombre:
        return INK_MUTED
    plantel = _roster()
    if nombre in plantel:
        indice = plantel.index(nombre)
    else:
        indice = sum(ord(c) for c in nombre)
    return CATEGORICOS[indice % len(CATEGORICOS)]


def hex_a_rgba(hex_color: str, alpha: float) -> str:
    """#RRGGBB + opacidad -> rgba(), para fondos y bordes tenues."""
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"
