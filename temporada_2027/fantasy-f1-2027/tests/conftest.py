"""
Base de datos para los tests.

Usa el Postgres de DATABASE_URL (por defecto el local). Arma una vez una base
plantilla con todas las migraciones, y cada test recibe una copia limpia: es
instantáneo y ningún test ve lo que dejó otro.
"""

import os
import uuid
from pathlib import Path

import psycopg
import pytest

RAIZ = Path(__file__).resolve().parent.parent
MIGRACIONES = sorted((RAIZ / "supabase" / "migrations").glob("*.sql"))
URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
PLANTILLA = "fantasy_plantilla"


def _url_de(base: str) -> str:
    return URL.rsplit("/", 1)[0] + "/" + base


@pytest.fixture(scope="session")
def plantilla():
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"drop database if exists {PLANTILLA}")
        admin.execute(f"create database {PLANTILLA}")
    with psycopg.connect(_url_de(PLANTILLA), autocommit=True) as conn:
        conn.execute((Path(__file__).parent / "supabase_local.sql").read_text())
        for m in MIGRACIONES:
            conn.execute(m.read_text())
    yield PLANTILLA
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"drop database if exists {PLANTILLA} with (force)")


@pytest.fixture
def db(plantilla):
    nombre = f"fantasy_test_{uuid.uuid4().hex[:10]}"
    with psycopg.connect(URL, autocommit=True) as admin:
        admin.execute(f"create database {nombre} template {plantilla}")
    conn = psycopg.connect(_url_de(nombre), autocommit=True)
    try:
        yield conn
    finally:
        conn.close()
        with psycopg.connect(URL, autocommit=True) as admin:
            admin.execute(f"drop database if exists {nombre} with (force)")


class Como:
    """Ejecuta consultas con los permisos de la página, como un usuario dado.

    Es exactamente lo que hace Supabase con cada pedido: cambia al rol
    `authenticated` (o `anon`) y deja el id del usuario en el token.
    """

    def __init__(self, conn, user_id=None):
        self.conn = conn
        self.user_id = user_id

    def execute(self, sql, params=None):
        rol = "authenticated" if self.user_id else "anon"
        with self.conn.transaction():
            self.conn.execute(f"set local role {rol}")
            self.conn.execute("select set_config('request.jwt.claim.sub', %s, true)",
                              (str(self.user_id or ""),))
            cur = self.conn.execute(sql, params)
            return cur.fetchall() if cur.description else None


@pytest.fixture
def como(db):
    return lambda user_id=None: Como(db, user_id)
