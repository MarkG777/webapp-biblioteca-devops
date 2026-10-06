"""
Pruebas del servidor TCP (socket_server.py) con pytest.

Una parte llama directamente a las funciones; otra levanta el servidor
real en un puerto libre y le envia comandos por TCP.
"""

import socket
import threading

import pytest

import socket_server as sock


def test_insert_autor_valido():
    r = sock.manejar_insert('{"tabla":"autores","nombre":"Julio Verne","nacionalidad":"Francia"}')
    assert '"statusCode": 200' in r
    assert "Julio Verne" in r


def test_insert_sin_tabla_responde_400():
    assert '"statusCode": 400' in sock.manejar_insert('{"nombre":"X"}')


def test_insert_tabla_desconocida_responde_400():
    assert '"statusCode": 400' in sock.manejar_insert('{"tabla":"inexistente","nombre":"X"}')


def test_insert_json_invalido_responde_400():
    assert '"statusCode": 400' in sock.manejar_insert("no es json")


def test_insert_que_no_es_objeto_responde_400():
    assert '"statusCode": 400' in sock.manejar_insert('["lista"]')


def test_insert_campos_obligatorios_faltantes_responde_400():
    assert "obligatorios faltantes" in sock.manejar_insert('{"tabla":"autores"}')


def test_insert_llave_foranea_invalida_responde_400():
    cuerpo = '{"tabla":"libros","titulo":"X","autor_id":999999,"categoria_id":999999}'
    assert '"statusCode": 400' in sock.manejar_insert(cuerpo)


def test_get_tabla_completa_y_por_id():
    sock.manejar_insert('{"tabla":"categorias","nombre":"Ensayo"}')
    completa = sock.manejar_get("categorias")
    assert "Ensayo" in completa
    por_id = sock.manejar_get("categorias:1")
    assert '"statusCode": 200' in por_id


def test_get_tabla_vacia():
    assert sock.manejar_get("autores") == '{"statusCode": 200, "data": []}\n'


def test_get_tabla_desconocida_responde_400():
    assert '"statusCode": 400' in sock.manejar_get("inexistente")


@pytest.fixture
def servidor_tcp():
    """Levanta el servidor real en un puerto libre (0 = el sistema elige)."""
    servidor = sock.Servidor(("127.0.0.1", 0), sock.Manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield servidor.server_address
    servidor.shutdown()
    servidor.server_close()


def enviar(direccion, linea):
    with socket.create_connection(direccion, timeout=5) as conn:
        conn.sendall((linea + "\n").encode("utf-8"))
        return conn.makefile("r", encoding="utf-8").readline()


def test_tcp_insert_y_get(servidor_tcp):
    respuesta = enviar(servidor_tcp, '{insert:{"tabla":"autores","nombre":"Euler","nacionalidad":"Suiza"}}')
    assert '"statusCode": 200' in respuesta
    assert "Euler" in enviar(servidor_tcp, "{get:autores}")


def test_tcp_formato_invalido_responde_400(servidor_tcp):
    assert '"statusCode": 400' in enviar(servidor_tcp, "hola")
