"""Prueba el protocolo TCP crudo {insert:...} / {get:...} en el puerto 6061."""

import json
import socket
import sys


def enviar(host, port, linea):
    with socket.create_connection((host, port), timeout=6) as s:
        s.sendall((linea + "\n").encode("utf-8"))
        s.settimeout(6)
        datos = b""
        while not datos.endswith(b"\n"):
            trozo = s.recv(4096)
            if not trozo:
                break
            datos += trozo
    return json.loads(datos.decode("utf-8"))


def check(host, port, linea, esperado_status, etiqueta):
    try:
        resp = enviar(host, port, linea)
        status = resp.get("statusCode")
        ok = status == esperado_status
        marca = "OK" if ok else "FALLO"
        print(f"{marca:6}{linea[:60]:62}{status} - {etiqueta}")
        if not ok:
            print("       respuesta:", resp)
        return ok, resp
    except Exception as exc:
        print(f"FALLO {linea[:60]:62}EXC - {etiqueta}: {exc}")
        return False, None


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 6061

    resultados = []

    ok, _ = check(host, port, '{get:autores}', 200, "listar autores (vacio o no)")
    resultados.append(ok)

    ok, resp = check(
        host, port,
        '{insert:{"tabla":"autores","nombre":"Julio Verne","nacionalidad":"Francia"}}',
        200, "insertar autor por socket",
    )
    resultados.append(ok)
    autor_id = resp["data"][0]["id"] if ok else None

    ok, _ = check(
        host, port,
        '{insert:{"tabla":"categorias","nombre":"Ciencia Ficcion"}}',
        200, "insertar categoria por socket",
    )
    resultados.append(ok)

    ok, _ = check(
        host, port,
        '{insert:{"tabla":"libros","titulo":"Veinte Mil Leguas","anio":1870,"autor_id":%s,"categoria_id":1}}' % autor_id,
        200, "insertar libro por socket",
    )
    resultados.append(ok)

    ok, _ = check(host, port, "{get:autores:%s}" % autor_id, 200, "obtener autor por id")
    resultados.append(ok)

    ok, _ = check(host, port, "{get:libros}", 200, "listar libros")
    resultados.append(ok)

    ok, _ = check(
        host, port,
        '{insert:{"tabla":"fantasma","nombre":"x"}}',
        400, "tabla invalida debe rechazarse",
    )
    resultados.append(ok)

    ok, _ = check(host, port, "{get:autores:999999}", 200, "id inexistente responde lista vacia")
    resultados.append(ok)

    print()
    if all(resultados):
        print("RESULTADO: TODO CORRECTO")
    else:
        print("RESULTADO: HAY FALLOS")
        sys.exit(1)


if __name__ == "__main__":
    main()
