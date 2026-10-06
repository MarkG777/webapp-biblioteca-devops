/**
 * Pruebas con Jest de la API HTTP (API Biblioteca).
 *
 * Los 10 endpoints de la practica, cada uno con 3 escenarios:
 *   1) exito     - datos validos, camino feliz.
 *   2) invalido  - datos faltantes, mal formados, o de tipo incorrecto.
 *   3) no-existe - id que no existe, formato de id invalido, o una regla
 *      de negocio que lo bloquea (llave foranea, duplicado, conflicto).
 *
 * Corre contra un servidor YA levantado (local o la EC2). Cambia BASE_URL
 * con una variable de entorno si no es localhost:
 *   BASE_URL=http://IP_EC2:8080 npm test
 */

const BASE = process.env.BASE_URL || "http://localhost:8080";

async function llamar(metodo, ruta, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(cuerpo);
  }
  const resp = await fetch(BASE + ruta, opciones);
  let json = null;
  try {
    json = await resp.json();
  } catch (_) {
    /* algunas respuestas de error no traen JSON */
  }
  return { status: resp.status, json };
}

async function llamarCrudo(metodo, ruta, textoPlano) {
  const resp = await fetch(BASE + ruta, { method: metodo, body: textoPlano });
  let json = null;
  try {
    json = await resp.json();
  } catch (_) {}
  return { status: resp.status, json };
}

function esperarEsquema(json) {
  expect(json).not.toBeNull();
  expect(Object.keys(json).sort()).toEqual(["data", "statusCode"]);
  expect(Array.isArray(json.data)).toBe(true);
}

let autorId;
let categoriaId;
let libroId;

beforeAll(async () => {
  await llamar("DELETE", "/api/db/vaciar");
});

// ============================================================
// 1. GET /api/autores
// ============================================================
describe("1. GET /api/autores", () => {
  test("[exito] lista vacia al inicio", async () => {
    const { status, json } = await llamar("GET", "/api/autores");
    expect(status).toBe(200);
    esperarEsquema(json);
    expect(json.data).toEqual([]);
  });

  test("[exito] lista con datos despues de insertar", async () => {
    const creado = await llamar("POST", "/api/autores", {
      nombre: "Gabriel Garcia Marquez",
      nacionalidad: "Colombia",
    });
    autorId = creado.json.data[0].id;
    const { status, json } = await llamar("GET", "/api/autores");
    expect(status).toBe(200);
    expect(json.data.some((a) => a.id === autorId)).toBe(true);
  });

  test("[no-existe] metodo no permitido (PATCH)", async () => {
    const { status } = await llamar("PATCH", "/api/autores");
    expect(status).toBe(405);
  });
});

// ============================================================
// 2. POST /api/autores
// ============================================================
describe("2. POST /api/autores", () => {
  test("[exito] crea un autor con datos validos", async () => {
    const { status, json } = await llamar("POST", "/api/autores", {
      nombre: "Isabel Allende",
      nacionalidad: "Chile",
    });
    expect(status).toBe(200);
    esperarEsquema(json);
    expect(json.data[0].nombre).toBe("Isabel Allende");
  });

  test("[invalido] falta el campo obligatorio 'nombre'", async () => {
    const { status } = await llamar("POST", "/api/autores", { nacionalidad: "Peru" });
    expect(status).toBe(400);
  });

  test("[invalido] el cuerpo no es JSON valido", async () => {
    const { status } = await llamarCrudo("POST", "/api/autores", "esto no es json");
    expect(status).toBe(400);
  });
});

// ============================================================
// 3. PUT /api/autores/:id
// ============================================================
describe("3. PUT /api/autores/:id", () => {
  test("[exito] actualiza un autor existente", async () => {
    const { status, json } = await llamar("PUT", `/api/autores/${autorId}`, {
      nombre: "Gabriel Garcia Marquez",
      nacionalidad: "Mexico",
    });
    expect(status).toBe(200);
    expect(json.data[0].nacionalidad).toBe("Mexico");
  });

  test("[no-existe] id que no existe (99999)", async () => {
    const { status } = await llamar("PUT", "/api/autores/99999", { nombre: "X" });
    expect(status).toBe(404);
  });

  test("[no-existe] id con formato invalido ('abc')", async () => {
    const { status } = await llamar("PUT", "/api/autores/abc", { nombre: "X" });
    expect(status).toBe(404);
  });
});

// ============================================================
// 5. GET /api/categorias  (numeracion sigue el orden del endpoints.http)
// ============================================================
describe("5. GET /api/categorias", () => {
  test("[exito] lista vacia al inicio", async () => {
    const { status, json } = await llamar("GET", "/api/categorias");
    expect(status).toBe(200);
    expect(json.data).toEqual([]);
  });

  test("[exito] lista con datos despues de insertar", async () => {
    const creada = await llamar("POST", "/api/categorias", { nombre: "Novela" });
    categoriaId = creada.json.data[0].id;
    const { status, json } = await llamar("GET", "/api/categorias");
    expect(status).toBe(200);
    expect(json.data.some((c) => c.id === categoriaId)).toBe(true);
  });

  test("[no-existe] metodo no permitido (DELETE sin id)", async () => {
    const { status } = await llamar("DELETE", "/api/categorias");
    expect(status).toBe(405);
  });
});

// ============================================================
// 6. POST /api/categorias
// ============================================================
describe("6. POST /api/categorias", () => {
  test("[exito] crea una categoria valida", async () => {
    const { status } = await llamar("POST", "/api/categorias", { nombre: "Ensayo" });
    expect(status).toBe(200);
  });

  test("[invalido] falta el campo obligatorio 'nombre'", async () => {
    const { status } = await llamar("POST", "/api/categorias", {});
    expect(status).toBe(400);
  });

  test("[no-existe] categoria duplicada (conflicto)", async () => {
    const { status } = await llamar("POST", "/api/categorias", { nombre: "Novela" });
    expect(status).toBe(409);
  });
});

// ============================================================
// 7. GET /api/libros
// ============================================================
describe("7. GET /api/libros", () => {
  test("[exito] lista vacia al inicio", async () => {
    const { status, json } = await llamar("GET", "/api/libros");
    expect(status).toBe(200);
    expect(json.data).toEqual([]);
  });

  test("[exito] lista con JOIN de autor y categoria", async () => {
    const creado = await llamar("POST", "/api/libros", {
      titulo: "Cien anios de soledad",
      anio: 1967,
      autor_id: autorId,
      categoria_id: categoriaId,
    });
    libroId = creado.json.data[0].id;
    const { status, json } = await llamar("GET", "/api/libros");
    expect(status).toBe(200);
    expect(json.data[0].autor).toBeDefined();
    expect(json.data[0].categoria).toBeDefined();
  });

  test("[no-existe] metodo no permitido (PATCH)", async () => {
    const { status } = await llamar("PATCH", "/api/libros");
    expect(status).toBe(405);
  });
});

// ============================================================
// 8. POST /api/libros
// ============================================================
describe("8. POST /api/libros", () => {
  test("[exito] crea un libro con datos validos", async () => {
    const { status } = await llamar("POST", "/api/libros", {
      titulo: "El amor en los tiempos del colera",
      anio: 1985,
      autor_id: autorId,
      categoria_id: categoriaId,
    });
    expect(status).toBe(200);
  });

  test("[invalido] falta el campo obligatorio 'titulo'", async () => {
    const { status } = await llamar("POST", "/api/libros", {
      autor_id: autorId,
      categoria_id: categoriaId,
    });
    expect(status).toBe(400);
  });

  test("[no-existe] autor_id / categoria_id no existen (llave foranea)", async () => {
    const { status } = await llamar("POST", "/api/libros", {
      titulo: "X",
      autor_id: 999999,
      categoria_id: 999999,
    });
    expect(status).toBe(400);
  });
});

// ============================================================
// 9. PUT /api/libros/:id
// ============================================================
describe("9. PUT /api/libros/:id", () => {
  test("[exito] actualiza un libro existente", async () => {
    const { status, json } = await llamar("PUT", `/api/libros/${libroId}`, {
      titulo: "Cien anios de soledad (edicion revisada)",
      anio: 1967,
      autor_id: autorId,
      categoria_id: categoriaId,
    });
    expect(status).toBe(200);
    expect(json.data[0].titulo).toBe("Cien anios de soledad (edicion revisada)");
  });

  test("[no-existe] id que no existe (99999)", async () => {
    const { status } = await llamar("PUT", "/api/libros/99999", {
      titulo: "X",
      autor_id: autorId,
      categoria_id: categoriaId,
    });
    expect(status).toBe(404);
  });

  test("[invalido] autor_id invalido al actualizar (llave foranea)", async () => {
    const { status } = await llamar("PUT", `/api/libros/${libroId}`, {
      titulo: "X",
      autor_id: 999999,
      categoria_id: categoriaId,
    });
    expect(status).toBe(400);
  });
});

// ============================================================
// 4. DELETE /api/autores/:id  (se prueba aqui, ya con el libro creado,
// para poder probar el caso de conflicto)
// ============================================================
describe("4. DELETE /api/autores/:id", () => {
  test("[no-existe] conflicto: autor con libros asociados (409)", async () => {
    const { status } = await llamar("DELETE", `/api/autores/${autorId}`);
    expect(status).toBe(409);
  });

  test("[no-existe] id que no existe (99999)", async () => {
    const { status } = await llamar("DELETE", "/api/autores/99999");
    expect(status).toBe(404);
  });

  test("[exito] borra un autor sin libros asociados", async () => {
    const otro = await llamar("POST", "/api/autores", { nombre: "Autor Temporal" });
    const { status } = await llamar("DELETE", `/api/autores/${otro.json.data[0].id}`);
    expect(status).toBe(200);
  });
});

// ============================================================
// 10. DELETE /api/libros/:id
// ============================================================
describe("10. DELETE /api/libros/:id", () => {
  test("[exito] borra un libro existente", async () => {
    const { status } = await llamar("DELETE", `/api/libros/${libroId}`);
    expect(status).toBe(200);
  });

  test("[no-existe] id que no existe (9999)", async () => {
    const { status } = await llamar("DELETE", "/api/libros/9999");
    expect(status).toBe(404);
  });

  test("[no-existe] id con formato invalido ('abc')", async () => {
    const { status } = await llamar("DELETE", "/api/libros/abc");
    expect(status).toBe(404);
  });
});

// ============================================================
// Extra: fuera de los 10 de esta practica (backup / vaciar),
// se mantienen porque la practica anterior los sigue requiriendo.
// ============================================================
describe("Extra (fuera del alcance de esta practica)", () => {
  test("[exito] POST /api/db/backup crea un respaldo", async () => {
    const { status, json } = await llamar("POST", "/api/db/backup");
    expect(status).toBe(200);
    expect(json.data[0].bytes).toBeGreaterThan(0);
  });

  test("[exito] DELETE /api/db/vaciar deja la base limpia", async () => {
    const { status } = await llamar("DELETE", "/api/db/vaciar");
    expect(status).toBe(200);
    const { json } = await llamar("GET", "/api/autores");
    expect(json.data).toEqual([]);
  });
});
