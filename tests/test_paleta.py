"""La paleta no se toca a ojo, y el color pertenece a la persona.

Los dos errores que cubren estos tests eran invisibles: los colores se veian
"bien" pero no se distinguian entre si, y cambiaban de dueño cuando alguien
se movia en la tabla.
"""

from f1.paleta import CATEGORICOS, ROJO_MARCA, color_participante

VALIDADOS = ["#3987e5", "#d95926", "#199e70", "#c98500",
             "#d55181", "#008300", "#9085e9", "#e66767"]


def test_la_paleta_es_la_que_paso_el_validador():
    # Si este test falla es porque alguien cambio un color a mano. Antes de
    # actualizar la lista de abajo hay que volver a correr:
    #   node validate_palette.js "<los 8>" --mode dark --surface "#111111"
    # y que diga ALL CHECKS PASS.
    assert CATEGORICOS == VALIDADOS


def test_el_rojo_de_marca_no_es_color_de_participante():
    # Si el rojo fuera las dos cosas, no se sabria si significa "esta persona"
    # o "prestá atencion".
    assert ROJO_MARCA not in CATEGORICOS


def test_el_color_pertenece_a_la_persona_no_al_puesto():
    # Antes el color salia del indice en la tabla ordenada por puntos: dos
    # personas que se pasaban en el ranking se intercambiaban los colores.
    antes = {n: color_participante(n) for n in ("miriquero", "friquero", "riquerole")}
    despues = {n: color_participante(n) for n in ("riquerole", "miriquero", "friquero")}
    assert antes == despues


def test_el_mismo_nombre_siempre_da_el_mismo_color():
    assert color_participante("miriquero") == color_participante("miriquero")


def test_un_nombre_desconocido_igual_recibe_un_color_estable():
    a = color_participante("alguien_que_no_esta")
    assert a in CATEGORICOS
    assert a == color_participante("alguien_que_no_esta")
