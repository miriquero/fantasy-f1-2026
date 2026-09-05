from f1.normalizacion import normalizar_nombre_carrera, normalizar_piloto


def test_normalizar_piloto_reconoce_nombre_canonico():
    assert normalizar_piloto("Max Verstappen") == "Max Verstappen"


def test_normalizar_piloto_traduce_variante_sin_tilde():
    assert normalizar_piloto("Nico Hulkenberg") == "Nico Hulkenberg"


def test_normalizar_piloto_traduce_alias_conocido():
    assert normalizar_piloto("Oliver Bearman") == "Ollie Bearman"
    assert normalizar_piloto("Alexander Albon") == "Alex Albon"
    assert normalizar_piloto("Andrea Kimi Antonelli") == "Kimi Antonelli"
    assert normalizar_piloto("Sergio Pérez") == "Sergio Perez"
    assert normalizar_piloto("Nico Hülkenberg") == "Nico Hulkenberg"
    assert normalizar_piloto("Gabriel Bortoleto") == "Gabriel Bortoletto"


def test_normalizar_piloto_desconocido_se_deja_igual():
    assert normalizar_piloto("Piloto Inventado") == "Piloto Inventado"


def test_normalizar_piloto_vacio():
    assert normalizar_piloto("") == ""


def test_normalizar_nombre_carrera_variantes_gran_bretana():
    # Estas son justo las variantes que causaban claves duplicadas en resultados.json
    assert normalizar_nombre_carrera("Gran Bretana") == "Gran Bretaña"
    assert normalizar_nombre_carrera("Gran_bretana") == "Gran Bretaña"
    assert normalizar_nombre_carrera("gran_bretana") == "Gran Bretaña"
    assert normalizar_nombre_carrera("Silverstone") == "Gran Bretaña"


def test_normalizar_nombre_carrera_sin_coincidencia_capitaliza():
    assert normalizar_nombre_carrera("nueva carrera") == "Nueva Carrera"


def test_normalizar_nombre_carrera_vacio():
    assert normalizar_nombre_carrera("") == ""
