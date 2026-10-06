/**
 * Pruebas con Jest del protocolo TCP crudo (puerto 6061).
 * No es HTTP: se manda una linea de texto {insert:...} o {get:...}
 * directo por un socket, y se espera una linea de JSON de respuesta.
 */

const net = require("net");

const HOST = process.env.SOCKET_HOST || "localhost";
const PORT = Number(process.env.SOCKET_PORT || 6061);

function mandar(comando) {
  return new Promise((resolve, reject) => {
    const socket = net.createConnection({ host: HOST, port: PORT }, () => {
      socket.write(comando + "\n");
    });
    let datos = "";
    socket.setTimeout(6000);
    socket.on("data", (trozo) => {
      datos += trozo.toString("utf8");
      if (datos.includes("\n")) {
        socket.end();
        resolve(JSON.parse(datos.trim()));
      }
    });
    socket.on("timeout", () => {
      socket.destroy();
      reject(new Error("timeout esperando respuesta del socket"));
    });
    socket.on("error", reject);
  });
}

describe("{get:...} por socket", () => {
  test("[exito] listar autores (vacio o no)", async () => {
    const resp = await mandar("{get:autores}");
    expect(resp.statusCode).toBe(200);
    expect(Array.isArray(resp.data)).toBe(true);
  });
});

describe("{insert:...} por socket", () => {
  let autorId;

  test("[exito] insertar autor por socket", async () => {
    const resp = await mandar('{insert:{"tabla":"autores","nombre":"Julio Verne","nacionalidad":"Francia"}}');
    expect(resp.statusCode).toBe(200);
    autorId = resp.data[0].id;
  });

  test("[invalido] tabla desconocida debe rechazarse", async () => {
    const resp = await mandar('{insert:{"tabla":"fantasma","nombre":"x"}}');
    expect(resp.statusCode).toBe(400);
  });

  test("[no-existe] obtener autor por id despues de insertarlo", async () => {
    const resp = await mandar(`{get:autores:${autorId}}`);
    expect(resp.statusCode).toBe(200);
    expect(resp.data.length).toBe(1);
  });

  test("[no-existe] id inexistente responde lista vacia", async () => {
    const resp = await mandar("{get:autores:999999}");
    expect(resp.statusCode).toBe(200);
    expect(resp.data).toEqual([]);
  });
});
