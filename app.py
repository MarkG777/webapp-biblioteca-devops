import os
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request

DB_PATH = os.environ.get("DB_PATH", os.path.join("data", "biblioteca.db"))
BACKUP_DIR = os.environ.get("BACKUP_DIR", "backups")

app = Flask(__name__)


def respond(status, data):
    """Toda respuesta cumple el esquema {statusCode, data}."""
    return jsonify({"statusCode": status, "data": data}), status


def error(status, message):
    return respond(status, [{"error": message}])


def get_db():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS categorias (
                id     INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE
            );
            CREATE TABLE IF NOT EXISTS autores (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre       TEXT NOT NULL,
                nacionalidad TEXT
            );
            CREATE TABLE IF NOT EXISTS libros (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo       TEXT NOT NULL,
                anio         INTEGER,
                autor_id     INTEGER NOT NULL REFERENCES autores(id)    ON DELETE RESTRICT,
                categoria_id INTEGER NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT
            );
            """
        )


def body_or_error(required):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return None, error(400, "El cuerpo debe ser un JSON valido")
    missing = [k for k in required if payload.get(k) in (None, "")]
    if missing:
        return None, error(400, "Campos obligatorios faltantes: " + ", ".join(missing))
    return payload, None


@app.errorhandler(404)
def not_found(_):
    return error(404, "Ruta no encontrada")


@app.errorhandler(405)
def method_not_allowed(_):
    return error(405, "Metodo no permitido")


@app.errorhandler(500)
def server_error(_):
    return error(500, "Error interno del servidor")


@app.get("/")
def index():
    endpoints = [
        "GET /api/autores",
        "POST /api/autores",
        "PUT /api/autores/<id>",
        "DELETE /api/autores/<id>",
        "GET /api/categorias",
        "POST /api/categorias",
        "GET /api/libros",
        "POST /api/libros",
        "PUT /api/libros/<id>",
        "DELETE /api/libros/<id>",
        "POST /api/db/backup",
        "DELETE /api/db/vaciar",
    ]
    return respond(200, [{"servicio": "API Biblioteca", "mensaje": "Prueba la buena uteq 12", "endpoints": endpoints}])


# ---------------------------- Autores ----------------------------
@app.get("/api/autores")
def listar_autores():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM autores ORDER BY id").fetchall()
    return respond(200, [dict(r) for r in rows])


@app.post("/api/autores")
def crear_autor():
    payload, err = body_or_error(["nombre"])
    if err:
        return err
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO autores (nombre, nacionalidad) VALUES (?, ?)",
            (payload["nombre"], payload.get("nacionalidad")),
        )
        row = conn.execute("SELECT * FROM autores WHERE id = ?", (cur.lastrowid,)).fetchone()
    return respond(200, [dict(row)])


@app.put("/api/autores/<int:autor_id>")
def actualizar_autor(autor_id):
    payload, err = body_or_error(["nombre"])
    if err:
        return err
    with get_db() as conn:
        cur = conn.execute(
            "UPDATE autores SET nombre = ?, nacionalidad = ? WHERE id = ?",
            (payload["nombre"], payload.get("nacionalidad"), autor_id),
        )
        if cur.rowcount == 0:
            return error(404, "Autor no encontrado")
        row = conn.execute("SELECT * FROM autores WHERE id = ?", (autor_id,)).fetchone()
    return respond(200, [dict(row)])


@app.delete("/api/autores/<int:autor_id>")
def eliminar_autor(autor_id):
    try:
        with get_db() as conn:
            cur = conn.execute("DELETE FROM autores WHERE id = ?", (autor_id,))
    except sqlite3.IntegrityError:
        return error(409, "El autor tiene libros asociados; eliminalos primero")
    if cur.rowcount == 0:
        return error(404, "Autor no encontrado")
    return respond(200, [{"eliminado": autor_id}])


# --------------------------- Categorias ---------------------------
@app.get("/api/categorias")
def listar_categorias():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM categorias ORDER BY id").fetchall()
    return respond(200, [dict(r) for r in rows])


@app.post("/api/categorias")
def crear_categoria():
    payload, err = body_or_error(["nombre"])
    if err:
        return err
    try:
        with get_db() as conn:
            cur = conn.execute("INSERT INTO categorias (nombre) VALUES (?)", (payload["nombre"],))
            row = conn.execute("SELECT * FROM categorias WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        return error(409, "La categoria ya existe")
    return respond(200, [dict(row)])


# ----------------------------- Libros -----------------------------
@app.get("/api/libros")
def listar_libros():
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT l.id, l.titulo, l.anio,
                   a.id AS autor_id, a.nombre AS autor,
                   c.id AS categoria_id, c.nombre AS categoria
            FROM libros l
            JOIN autores a    ON a.id = l.autor_id
            JOIN categorias c ON c.id = l.categoria_id
            ORDER BY l.id
            """
        ).fetchall()
    return respond(200, [dict(r) for r in rows])


@app.post("/api/libros")
def crear_libro():
    payload, err = body_or_error(["titulo", "autor_id", "categoria_id"])
    if err:
        return err
    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO libros (titulo, anio, autor_id, categoria_id) VALUES (?, ?, ?, ?)",
                (payload["titulo"], payload.get("anio"), payload["autor_id"], payload["categoria_id"]),
            )
            row = conn.execute("SELECT * FROM libros WHERE id = ?", (cur.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        return error(400, "autor_id o categoria_id no existen")
    return respond(200, [dict(row)])


@app.put("/api/libros/<int:libro_id>")
def actualizar_libro(libro_id):
    payload, err = body_or_error(["titulo", "autor_id", "categoria_id"])
    if err:
        return err
    try:
        with get_db() as conn:
            cur = conn.execute(
                "UPDATE libros SET titulo = ?, anio = ?, autor_id = ?, categoria_id = ? WHERE id = ?",
                (payload["titulo"], payload.get("anio"), payload["autor_id"], payload["categoria_id"], libro_id),
            )
            if cur.rowcount == 0:
                return error(404, "Libro no encontrado")
            row = conn.execute("SELECT * FROM libros WHERE id = ?", (libro_id,)).fetchone()
    except sqlite3.IntegrityError:
        return error(400, "autor_id o categoria_id no existen")
    return respond(200, [dict(row)])


@app.delete("/api/libros/<int:libro_id>")
def eliminar_libro(libro_id):
    with get_db() as conn:
        cur = conn.execute("DELETE FROM libros WHERE id = ?", (libro_id,))
    if cur.rowcount == 0:
        return error(404, "Libro no encontrado")
    return respond(200, [{"eliminado": libro_id}])


# ------------------------ Backup y vaciado ------------------------
@app.post("/api/db/backup")
def backup_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    nombre = "biblioteca_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".db"
    destino = os.path.join(BACKUP_DIR, nombre)
    origen = get_db()
    copia = sqlite3.connect(destino)
    try:
        origen.backup(copia)
    finally:
        copia.close()
        origen.close()
    return respond(200, [{"archivo": nombre, "bytes": os.path.getsize(destino)}])


@app.delete("/api/db/vaciar")
def vaciar_db():
    tablas = ["libros", "autores", "categorias"]
    eliminadas = {}
    with get_db() as conn:
        for tabla in tablas:
            eliminadas[tabla] = conn.execute("DELETE FROM " + tabla).rowcount
        conn.execute("DELETE FROM sqlite_sequence")
    return respond(200, [{"filas_eliminadas": eliminadas}])


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 80)))
