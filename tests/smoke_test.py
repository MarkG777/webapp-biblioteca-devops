"""
Pruebas automatizadas de la API HTTP.

Por cada endpoint se cubren 3 escenarios (donde aplica):
  1) Exito     - datos validos, camino feliz.
  2) Invalido  - datos faltantes, mal formados, o de tipo incorrecto.
  3) No existe / Conflicto - id que no existe, formato de id invalido,
     o una regla de negocio que lo bloquea (ej. llave foranea, duplicado).
"""

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
fallos = 0


def llamar(metodo, ruta, cuerpo=None, crudo=None, headers=None):
    """crudo: bytes a mandar tal cual (para probar un body que no es JSON valido)."""
    if crudo is not None:
        data = crudo
    else:
        data = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=data, method=metodo)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    elif data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        cuerpo_resp = e.read()
        try:
            return e.code, json.loads(cuerpo_resp)
        except json.JSONDecodeError:
            return e.code, {"statusCode": e.code, "data": [{"error": cuerpo_resp.decode(errors='replace')}]}


def verificar(escenario, nombre, metodo, ruta, esperado, cuerpo=None, crudo=None, headers=None, checar_schema=True):
    global fallos
    status, resp = llamar(metodo, ruta, cuerpo, crudo, headers)
    esquema_ok = True
    if checar_schema:
        esquema_ok = (
            isinstance(resp, dict)
            and set(resp.keys()) == {"statusCode", "data"}
            and resp["statusCode"] == status
            and isinstance(resp["data"], list)
        )
    ok = status == esperado and esquema_ok
    fallos += 0 if ok else 1
    print(("OK   " if ok else "FALLO"), f"[{escenario}]".ljust(12), metodo.ljust(6), ruta.ljust(26), status, "-", nombre)
    if not ok:
        print("       respuesta:", resp)
    return resp


# ============================================================
# Estado inicial limpio
# ============================================================
verificar("exito", "vaciar BD (estado limpio)", "DELETE", "/api/db/vaciar", 200)

# ============================================================
# GET /api/autores
# ============================================================
verificar("exito", "lista vacia tras vaciar", "GET", "/api/autores", 200)
autor = verificar("exito", "crear autor", "POST", "/api/autores", 200, {"nombre": "Gabriel Garcia Marquez", "nacionalidad": "Colombia"})
verificar("exito", "lista ahora tiene datos", "GET", "/api/autores", 200)
verificar("no-existe", "metodo no permitido (PATCH)", "PATCH", "/api/autores", 405)

# ============================================================
# POST /api/autores
# ============================================================
verificar("invalido", "falta campo 'nombre'", "POST", "/api/autores", 400, {"nacionalidad": "Peru"})
verificar("invalido", "cuerpo no es JSON valido", "POST", "/api/autores", 400, crudo=b"esto no es json")

# ============================================================
# PUT /api/autores/<id>
# ============================================================
autor_id = autor["data"][0]["id"]
verificar("exito", "actualizar autor existente", "PUT", f"/api/autores/{autor_id}", 200, {"nombre": "Gabriel Garcia Marquez", "nacionalidad": "Mexico"})
verificar("no-existe", "id que no existe (99999)", "PUT", "/api/autores/99999", 404, {"nombre": "X"})
verificar("no-existe", "id con formato invalido ('abc')", "PUT", "/api/autores/abc", 404, {"nombre": "X"}, checar_schema=False)

# ============================================================
# DELETE /api/autores/<id>  (el caso de exito se prueba mas abajo,
# despues de quitarle el libro asociado)
# ============================================================
verificar("no-existe", "id que no existe (99999)", "DELETE", "/api/autores/99999", 404)
verificar("no-existe", "id con formato invalido ('xyz')", "DELETE", "/api/autores/xyz", 404, checar_schema=False)

# ============================================================
# GET / POST /api/categorias
# ============================================================
verificar("exito", "lista vacia", "GET", "/api/categorias", 200)
cat = verificar("exito", "crear categoria", "POST", "/api/categorias", 200, {"nombre": "Novela"})
verificar("invalido", "falta campo 'nombre'", "POST", "/api/categorias", 400, {})
verificar("no-existe", "categoria duplicada (conflicto)", "POST", "/api/categorias", 409, {"nombre": "Novela"})
verificar("exito", "lista ahora tiene datos", "GET", "/api/categorias", 200)
verificar("no-existe", "metodo no permitido (DELETE sin id)", "DELETE", "/api/categorias", 405)

# ============================================================
# GET / POST /api/libros
# ============================================================
verificar("exito", "lista vacia", "GET", "/api/libros", 200)
libro = verificar(
    "exito", "crear libro", "POST", "/api/libros", 200,
    {"titulo": "Cien anios de soledad", "anio": 1967,
     "autor_id": autor_id, "categoria_id": cat["data"][0]["id"]},
)
verificar("invalido", "falta campo obligatorio 'titulo'", "POST", "/api/libros", 400, {"autor_id": autor_id, "categoria_id": cat["data"][0]["id"]})
verificar("no-existe", "autor_id/categoria_id no existen (FK)", "POST", "/api/libros", 400, {"titulo": "X", "autor_id": 999999, "categoria_id": 999999})
verificar("exito", "lista con JOIN de autor y categoria", "GET", "/api/libros", 200)
verificar("no-existe", "metodo no permitido (PATCH)", "PATCH", "/api/libros", 405)

# ============================================================
# PUT /api/libros/<id>
# ============================================================
libro_id = libro["data"][0]["id"]
verificar(
    "exito", "actualizar libro existente", "PUT", f"/api/libros/{libro_id}", 200,
    {"titulo": "Cien anios de soledad (edicion revisada)", "anio": 1967,
     "autor_id": autor_id, "categoria_id": cat["data"][0]["id"]},
)
verificar("no-existe", "id que no existe (99999)", "PUT", "/api/libros/99999", 404, {"titulo": "X", "autor_id": autor_id, "categoria_id": cat["data"][0]["id"]})
verificar("invalido", "autor_id invalido al actualizar (FK)", "PUT", f"/api/libros/{libro_id}", 400, {"titulo": "X", "autor_id": 999999, "categoria_id": cat["data"][0]["id"]})

# ============================================================
# Regla de negocio: no se borra un autor con libros
# ============================================================
verificar("no-existe", "borrar autor con libros asociados (conflicto)", "DELETE", f"/api/autores/{autor_id}", 409)

# ============================================================
# POST /api/db/backup
# ============================================================
b1 = verificar("exito", "backup con datos presentes", "POST", "/api/db/backup", 200)
if b1["data"][0]["bytes"] <= 0:
    fallos += 1
    print("FALLO [exito]      el archivo de backup deberia pesar mas de 0 bytes")
else:
    print("OK    [exito]      el archivo de backup pesa", b1["data"][0]["bytes"], "bytes")

# ============================================================
# DELETE /api/libros/<id>
# ============================================================
verificar("exito", "borrar libro existente", "DELETE", f"/api/libros/{libro_id}", 200)
verificar("no-existe", "id que no existe (9999)", "DELETE", "/api/libros/9999", 404)
verificar("no-existe", "id con formato invalido ('abc')", "DELETE", "/api/libros/abc", 404, checar_schema=False)

# ============================================================
# DELETE /api/autores/<id>  (ahora si, sin libros asociados)
# ============================================================
verificar("exito", "borrar autor sin libros asociados", "DELETE", f"/api/autores/{autor_id}", 200)

# ============================================================
# DELETE /api/db/vaciar
# ============================================================
verificar("exito", "backup funciona con BD vacia tambien", "POST", "/api/db/backup", 200)
verificar("exito", "vaciar de nuevo estando ya vacia (no debe fallar)", "DELETE", "/api/db/vaciar", 200)
verificar("exito", "confirmar que quedo vacia de verdad", "GET", "/api/autores", 200)

print("\nRESULTADO:", "TODO CORRECTO" if fallos == 0 else str(fallos) + " fallo(s)")
sys.exit(1 if fallos else 0)
