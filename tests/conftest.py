"""
Configuracion comun de pytest.

La base de datos apunta a una carpeta temporal ANTES de importar app.py,
porque app.py lee DB_PATH al cargarse. Asi las pruebas nunca tocan
data/biblioteca.db.
"""

import os
import sys
import tempfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

_temporal = tempfile.mkdtemp()
os.environ["DB_PATH"] = os.path.join(_temporal, "prueba.db")
os.environ["BACKUP_DIR"] = os.path.join(_temporal, "backups")

import pytest  # noqa: E402

import app as app_mod  # noqa: E402


@pytest.fixture(autouse=True)
def base_vacia():
    """Cada prueba empieza con la base vacia."""
    with app_mod.get_db() as conn:
        conn.execute("DELETE FROM libros")
        conn.execute("DELETE FROM autores")
        conn.execute("DELETE FROM categorias")
        conn.execute("DELETE FROM sqlite_sequence")
    yield


@pytest.fixture
def cliente():
    app_mod.app.config["TESTING"] = True
    with app_mod.app.test_client() as c:
        yield c
