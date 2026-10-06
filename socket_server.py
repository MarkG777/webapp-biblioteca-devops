"""
Servidor TCP crudo (sin HTTP) para la mejora de la practica.

Protocolo, una linea de texto terminada en salto de linea:

    {insert:<json>}   -> inserta un elemento. <json> es el mismo cuerpo
                          que ya se usaba en los POST de la practica anterior,
                          mas una llave "tabla" que dice donde insertarlo.
                          Ejemplo:
                          {insert:{"tabla":"autores","nombre":"Julio Verne","nacionalidad":"Francia"}}

    {get:<tabla>}         -> devuelve todas las filas de esa tabla.
    {get:<tabla>:<id>}    -> devuelve una sola fila por id.
                          Ejemplo: {get:autores} o {get:autores:3}

Tablas validas: autores, categorias, libros (las mismas de app.py).
Responde SIEMPRE una linea de JSON con el mismo esquema {statusCode, data}
que ya usa la API HTTP, para mantener consistencia entre los dos protocolos.
"""

import json
import re
import socketserver

from app import get_db, init_db

HOST = "0.0.0.0"
PORT = 6061

COMANDO_RE = re.compile(r"^\{(insert|get):(.*)\}\s*$", re.DOTALL)

TABLAS = {
    "autores": {
        "columnas": ["nombre", "nacionalidad"],
        "obligatorios": ["nombre"],
    },
    "categorias": {
        "columnas": ["nombre"],
        "obligatorios": ["nombre"],
    },
    "libros": {
        "columnas": ["titulo", "anio", "autor_id", "categoria_id"],
        "obligatorios": ["titulo", "autor_id", "categoria_id"],
    },
}


def responder(status, data):
    return json.dumps({"statusCode": status, "data": data}, ensure_ascii=False) + "\n"


def manejar_insert(cuerpo):
    try:
        payload = json.loads(cuerpo)
    except json.JSONDecodeError:
        return responder(400, [{"error": "JSON invalido dentro de {insert:...}"}])

    if not isinstance(payload, dict):
        return responder(400, [{"error": "el elemento debe ser un objeto JSON"}])

    tabla = payload.get("tabla")
    if tabla not in TABLAS:
        return responder(400, [{"error": "tabla desconocida: " + str(tabla) + ". usa autores, categorias o libros"}])

    spec = TABLAS[tabla]
    faltantes = [c for c in spec["obligatorios"] if payload.get(c) in (None, "")]
    if faltantes:
        return responder(400, [{"error": "campos obligatorios faltantes: " + ", ".join(faltantes)}])

    columnas = [c for c in spec["columnas"] if c in payload]
    valores = [payload[c] for c in columnas]
    marcadores = ", ".join("?" for _ in columnas)

    try:
        with get_db() as conn:
            cur = conn.execute(
                "INSERT INTO " + tabla + " (" + ", ".join(columnas) + ") VALUES (" + marcadores + ")",
                valores,
            )
            fila = conn.execute("SELECT * FROM " + tabla + " WHERE id = ?", (cur.lastrowid,)).fetchone()
    except Exception as exc:
        return responder(400, [{"error": str(exc)}])

    return responder(200, [dict(fila)])


def manejar_get(cuerpo):
    partes = cuerpo.split(":")
    tabla = partes[0]
    if tabla not in TABLAS:
        return responder(400, [{"error": "tabla desconocida: " + str(tabla)}])

    with get_db() as conn:
        if len(partes) > 1 and partes[1] != "":
            filas = conn.execute("SELECT * FROM " + tabla + " WHERE id = ?", (partes[1],)).fetchall()
        else:
            filas = conn.execute("SELECT * FROM " + tabla + " ORDER BY id").fetchall()

    return responder(200, [dict(f) for f in filas])


class Manejador(socketserver.StreamRequestHandler):
    def handle(self):
        linea = self.rfile.readline().decode("utf-8", errors="replace").strip()
        if not linea:
            return

        coincidencia = COMANDO_RE.match(linea)
        if not coincidencia:
            self.wfile.write(
                responder(400, [{"error": "formato esperado: {insert:<json>} o {get:<tabla>[:<id>]}"}]).encode("utf-8")
            )
            return

        comando, cuerpo = coincidencia.group(1), coincidencia.group(2)
        if comando == "insert":
            salida = manejar_insert(cuerpo)
        else:
            salida = manejar_get(cuerpo)

        self.wfile.write(salida.encode("utf-8"))


class Servidor(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    init_db()
    print("Socket TCP escuchando en %s:%s" % (HOST, PORT), flush=True)
    with Servidor((HOST, PORT), Manejador) as servidor:
        servidor.serve_forever()
