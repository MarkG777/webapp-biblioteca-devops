"""
Pruebas unitarias de la API Flask (app.py) con pytest.

Llaman a la app con el test_client de Flask, sin levantar servidor.
Sirven para medir la cobertura del codigo Python (pytest-cov).
"""


def crear_autor(cliente, nombre="Gabriel Garcia Marquez", nacionalidad="Colombia"):
    r = cliente.post("/api/autores", json={"nombre": nombre, "nacionalidad": nacionalidad})
    return r.get_json()["data"][0]["id"]


def crear_categoria(cliente, nombre="Novela"):
    r = cliente.post("/api/categorias", json={"nombre": nombre})
    return r.get_json()["data"][0]["id"]


def crear_libro(cliente, autor_id, categoria_id, titulo="Cien anios de soledad"):
    r = cliente.post(
        "/api/libros",
        json={"titulo": titulo, "anio": 1967, "autor_id": autor_id, "categoria_id": categoria_id},
    )
    return r.get_json()["data"][0]["id"]


# ---------------------------- General ----------------------------
def test_index_lista_los_endpoints(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "GET /api/autores" in r.get_json()["data"][0]["endpoints"]


def test_ruta_inexistente_responde_404_con_esquema(cliente):
    r = cliente.get("/no-existe")
    assert r.status_code == 404
    assert set(r.get_json().keys()) == {"statusCode", "data"}


def test_metodo_no_permitido_responde_405(cliente):
    assert cliente.patch("/api/autores").status_code == 405


# ----------------------------- Autores -----------------------------
def test_listar_autores_vacio(cliente):
    r = cliente.get("/api/autores")
    assert r.status_code == 200
    assert r.get_json()["data"] == []


def test_crear_autor_valido(cliente):
    r = cliente.post("/api/autores", json={"nombre": "Isabel Allende", "nacionalidad": "Chile"})
    assert r.status_code == 200
    assert r.get_json()["data"][0]["nombre"] == "Isabel Allende"


def test_crear_autor_sin_nombre_responde_400(cliente):
    r = cliente.post("/api/autores", json={"nacionalidad": "Peru"})
    assert r.status_code == 400


def test_crear_autor_con_cuerpo_no_json_responde_400(cliente):
    r = cliente.post("/api/autores", data="esto no es json", content_type="text/plain")
    assert r.status_code == 400


def test_actualizar_autor_existente(cliente):
    autor = crear_autor(cliente)
    r = cliente.put(f"/api/autores/{autor}", json={"nombre": "Gabriel", "nacionalidad": "Mexico"})
    assert r.status_code == 200
    assert r.get_json()["data"][0]["nacionalidad"] == "Mexico"


def test_actualizar_autor_inexistente_responde_404(cliente):
    r = cliente.put("/api/autores/99999", json={"nombre": "X"})
    assert r.status_code == 404


def test_eliminar_autor_con_libros_responde_409(cliente):
    autor = crear_autor(cliente)
    crear_libro(cliente, autor, crear_categoria(cliente))
    assert cliente.delete(f"/api/autores/{autor}").status_code == 409


def test_eliminar_autor_inexistente_responde_404(cliente):
    assert cliente.delete("/api/autores/99999").status_code == 404


def test_eliminar_autor_sin_libros(cliente):
    autor = crear_autor(cliente)
    assert cliente.delete(f"/api/autores/{autor}").status_code == 200


# ---------------------------- Categorias ----------------------------
def test_listar_categorias_con_datos(cliente):
    crear_categoria(cliente)
    r = cliente.get("/api/categorias")
    assert [c["nombre"] for c in r.get_json()["data"]] == ["Novela"]


def test_crear_categoria_duplicada_responde_409(cliente):
    crear_categoria(cliente)
    assert cliente.post("/api/categorias", json={"nombre": "Novela"}).status_code == 409


def test_crear_categoria_sin_nombre_responde_400(cliente):
    assert cliente.post("/api/categorias", json={}).status_code == 400


# ------------------------------ Libros ------------------------------
def test_listar_libros_con_join(cliente):
    autor = crear_autor(cliente)
    crear_libro(cliente, autor, crear_categoria(cliente))
    libro = cliente.get("/api/libros").get_json()["data"][0]
    assert libro["autor"] == "Gabriel Garcia Marquez"
    assert libro["categoria"] == "Novela"


def test_crear_libro_sin_titulo_responde_400(cliente):
    autor = crear_autor(cliente)
    r = cliente.post("/api/libros", json={"autor_id": autor, "categoria_id": crear_categoria(cliente)})
    assert r.status_code == 400


def test_crear_libro_con_llave_foranea_invalida_responde_400(cliente):
    r = cliente.post("/api/libros", json={"titulo": "X", "autor_id": 999999, "categoria_id": 999999})
    assert r.status_code == 400


def test_actualizar_libro_existente(cliente):
    autor = crear_autor(cliente)
    categoria = crear_categoria(cliente)
    libro = crear_libro(cliente, autor, categoria)
    r = cliente.put(
        f"/api/libros/{libro}",
        json={"titulo": "Edicion revisada", "anio": 1967, "autor_id": autor, "categoria_id": categoria},
    )
    assert r.status_code == 200
    assert r.get_json()["data"][0]["titulo"] == "Edicion revisada"


def test_actualizar_libro_inexistente_responde_404(cliente):
    autor = crear_autor(cliente)
    categoria = crear_categoria(cliente)
    r = cliente.put("/api/libros/99999", json={"titulo": "X", "autor_id": autor, "categoria_id": categoria})
    assert r.status_code == 404


def test_actualizar_libro_con_llave_foranea_invalida_responde_400(cliente):
    autor = crear_autor(cliente)
    categoria = crear_categoria(cliente)
    libro = crear_libro(cliente, autor, categoria)
    r = cliente.put(f"/api/libros/{libro}", json={"titulo": "X", "autor_id": 999999, "categoria_id": categoria})
    assert r.status_code == 400


def test_eliminar_libro_existente_e_inexistente(cliente):
    autor = crear_autor(cliente)
    libro = crear_libro(cliente, autor, crear_categoria(cliente))
    assert cliente.delete(f"/api/libros/{libro}").status_code == 200
    assert cliente.delete(f"/api/libros/{libro}").status_code == 404


# ------------------------ Backup y vaciado ------------------------
def test_backup_crea_archivo(cliente):
    r = cliente.post("/api/db/backup")
    assert r.status_code == 200
    assert r.get_json()["data"][0]["bytes"] > 0


def test_vaciar_deja_la_base_limpia(cliente):
    crear_autor(cliente)
    assert cliente.delete("/api/db/vaciar").status_code == 200
    assert cliente.get("/api/autores").get_json()["data"] == []
