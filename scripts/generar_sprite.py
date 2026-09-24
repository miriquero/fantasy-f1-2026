# -*- coding: utf-8 -*-
"""Genera el sprite SVG de banderas y trazados de circuito.

Por que existe: las banderas eran emoji, y Windows no trae ninguna fuente que
sepa dibujarlas -- son dos letras invisibles que la fuente debe combinar. En
los telefonos se veian; en una PC no. Se reemplazan por SVG de verdad.

Los trazados salen de un dataset abierto de F1 (GeoJSON con las coordenadas de
cada circuito) y se dibujan aca como paths. No son fotos: una foto de circuito
tiene derechos y pesa megas; el trazado se reconoce igual y pesa un kilobyte.

Salida: f1/templates/sprite.svg, un solo archivo con todos los simbolos, que
se incrusta una vez y se referencia con <use>.
"""
import json
import re
import unicodedata
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SALIDA = REPO / "f1" / "templates" / "sprite.svg"

CDN_BANDERAS = "https://cdn.jsdelivr.net/npm/flag-icons@7/flags/4x3/{}.svg"
GEOJSON = "https://raw.githubusercontent.com/bacinger/f1-circuits/master/f1-circuits.geojson"

# Carrera -> (codigo ISO de la bandera, texto que identifica al circuito)
CARRERAS = {
    "Australia":     ("au", "albert park"),
    "China":         ("cn", "shanghai"),
    "Japon":         ("jp", "suzuka"),
    "Miami":         ("us", "miami"),
    "Canada":        ("ca", "villeneuve"),
    "Monaco":        ("mc", "monaco"),
    "Barcelona":     ("es", "barcelona"),
    "Austria":       ("at", "red bull ring"),
    "Gran Bretaña":  ("gb", "silverstone"),
    "Belgica":       ("be", "spa"),
    "Hungría":       ("hu", "hungaroring"),
    "Países Bajos":  ("nl", "zandvoort"),
    "Italia":        ("it", "monza"),
    "Madrid":        ("es", "madrid"),
    "Azerbaiyan":    ("az", "baku"),
    "Bahrein":       ("bh", "sepang"),
    "Singapur":      ("sg", "marina bay"),
    "Austin":        ("us", "americas"),
    "Mexico":        ("mx", "rodriguez"),
    "Brasil":        ("br", "interlagos"),
    "Las Vegas":     ("us", "las vegas"),
    "Qatar":         ("qa", "losail"),
    "Abu Dhabi":     ("ae", "yas marina"),
    # Cancelada, pero la tarjeta se muestra tachada en el calendario: si no
    # tuviera simbolo, su <use> apuntaria a un id inexistente.
    "Arabia Saudita": ("sa", "jeddah"),
}

# Mexico y España pesan 83 y 79 KB por el escudo, que a 24 px de alto no se
# ve. Se dibujan simplificadas: a ese tamaño son indistinguibles y ahorran
# 160 KB, casi la mitad del peso de la pagina.
SIMPLIFICADAS = {
    "mx": '<rect width="4" height="3" fill="#ce1126"/>'
          '<rect width="2.667" height="3" fill="#fff"/>'
          '<rect width="1.333" height="3" fill="#006847"/>',
    "es": '<rect width="4" height="3" fill="#c60b1e"/>'
          '<rect y="0.75" width="4" height="1.5" fill="#ffc400"/>',
}


def bajar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8")


def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def simbolo_bandera(cc):
    """<symbol> con el contenido de la bandera, normalizado a viewBox 0 0 4 3."""
    if cc in SIMPLIFICADAS:
        return f'<symbol id="b-{cc}" viewBox="0 0 4 3">{SIMPLIFICADAS[cc]}</symbol>'
    svg = bajar(CDN_BANDERAS.format(cc))
    vb = re.search(r'viewBox="([^"]+)"', svg)
    interior = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", svg, flags=re.S).strip()
    interior = re.sub(r"<\?xml.*?\?>|<!DOCTYPE.*?>", "", interior, flags=re.S).strip()
    return f'<symbol id="b-{cc}" viewBox="{vb.group(1) if vb else "0 0 640 480"}">{interior}</symbol>'


def trazados():
    """{texto del circuito: path SVG} a partir del GeoJSON abierto."""
    datos = json.loads(bajar(GEOJSON))
    salida = {}
    for f in datos["features"]:
        p = f["properties"]
        etiqueta = sin_acentos(f"{p.get('Name','')} {p.get('Location','')} {p.get('id','')}")
        coords = f["geometry"]["coordinates"]
        while coords and isinstance(coords[0][0], list):
            coords = coords[0]
        if len(coords) < 10:
            continue
        salida[etiqueta] = coords
    return salida


def simbolo_circuito(nombre, coords):
    """Normaliza lat/lon a un viewBox de 100x100 y arma el path."""
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    ancho, alto = (maxx - minx) or 1e-9, (maxy - miny) or 1e-9
    escala = 92 / max(ancho, alto)
    dx = (100 - ancho * escala) / 2
    dy = (100 - alto * escala) / 2

    # Se quedan uno de cada N puntos: el trazado a 60 px de ancho se ve igual
    # y el path pasa de varios KB a unos cientos de bytes.
    paso = max(1, len(coords) // 120)
    puntos = []
    for x, y in coords[::paso]:
        px = (x - minx) * escala + dx
        py = 100 - ((y - miny) * escala + dy)      # el eje Y del SVG va al reves
        puntos.append(f"{px:.1f},{py:.1f}")
    d = "M" + "L".join(puntos) + "Z"
    return (f'<symbol id="c-{nombre}" viewBox="0 0 100 100">'
            f'<path d="{d}" fill="none" stroke="currentColor" stroke-width="5" '
            f'stroke-linejoin="round" stroke-linecap="round"/></symbol>')


def main():
    pistas = trazados()
    simbolos, faltantes = [], []
    vistos = set()

    for carrera, (cc, clave) in CARRERAS.items():
        if cc not in vistos:
            simbolos.append(simbolo_bandera(cc))
            vistos.add(cc)
        candidatos = [k for k in pistas if clave in k]
        if not candidatos:
            faltantes.append(carrera)
            continue
        ident = sin_acentos(carrera).replace(" ", "-")
        simbolos.append(simbolo_circuito(ident, pistas[candidatos[0]]))

    # xmlns:xlink hace falta porque alguna bandera (la de China) usa xlink:href
    # adentro, y al quitarle el <svg> exterior perdio la declaracion del
    # prefijo. Sin esto el sprite no es XML valido.
    sprite = ('<svg xmlns="http://www.w3.org/2000/svg" '
              'xmlns:xlink="http://www.w3.org/1999/xlink" '
              'style="display:none" aria-hidden="true">'
              + "".join(simbolos) + "</svg>\n")
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(sprite, encoding="utf-8", newline="\n")

    print(f"sprite escrito: {SALIDA.relative_to(REPO)}")
    print(f"  banderas : {len(vistos)}")
    print(f"  circuitos: {len(CARRERAS) - len(faltantes)} de {len(CARRERAS)}")
    if faltantes:
        print(f"  SIN TRAZADO: {faltantes}")
    print(f"  peso     : {SALIDA.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    main()
