# Practica: Ejecutar Web App en Contenedor

API REST "Biblioteca" (Flask + SQLite) empaquetada en Docker.

- Base de datos normalizada (3FN): `categorias`, `autores`, `libros` (con llaves foraneas).
- 10 endpoints; toda respuesta cumple `{ "statusCode": 200, "data": [] }`.
- Incluye GET, POST y DELETE, mas backup (`POST /api/db/backup`) y vaciado (`DELETE /api/db/vaciar`).

## Estado

| Parte | Estado |
|---|---|
| 1. Web App + SQLite + 10 endpoints | Hecho y probado (`tests/smoke_test.py`) |
| 2. Dockerfile, build y run local en :8080 | Hecho y probado |
| 3. Cuenta AWS + EC2 Ubuntu + Docker | Lo haces tu (cuenta personal) |
| 4. Subir imagen a Docker Hub | Lo haces tu (`docker login`) |
| 5. Despliegue en EC2 y pruebas | Lo haces tu |

## Comandos locales (Parte 2)

    docker build -t webapp:latest .
    docker run -d -p 8080:80 --name webapp-container webapp:latest
    python tests/smoke_test.py http://localhost:8080

## Parte 4: Docker Hub (reemplaza TU_USUARIO)

    docker login
    docker tag webapp:latest TU_USUARIO/webapp:latest
    docker push TU_USUARIO/webapp:latest

## Parte 3 y 5: EC2 (Ubuntu Server)

1. Lanzar UNA sola instancia EC2 con Ubuntu Server (t2.micro / t3.micro, Free Tier).
2. Security Group: permitir entrada TCP 22 (SSH) y TCP 8080 (Anywhere o tu IP).
3. Conectarse por SSH (o "EC2 Instance Connect") e instalar Docker:

        sudo apt-get update
        sudo apt-get install -y docker.io
        sudo systemctl enable --now docker
        sudo usermod -aG docker ubuntu   # cerrar y volver a abrir la sesion

4. Descargar y ejecutar:

        docker pull TU_USUARIO/webapp:latest
        docker run -d -p 8080:80 --name webapp-container TU_USUARIO/webapp:latest

5. Probar cada endpoint con `endpoints.http` o Postman usando `http://IP_PUBLICA_EC2:8080`.

## Capturas para el documento (11 en total, guardar en `evidencias/`)

Se mezclan capturas de terminal (bash/PowerShell) y de pantalla completa.
Solo se crea UNA instancia EC2 para toda la practica.

Ya generadas (terminal, a partir de la salida real):

1. `01-docker-build.png` - `docker build -t webapp:latest .`
2. `02-docker-run-ps-curl.png` - `docker run`, `docker ps` y `curl localhost:8080`
3. `03-prueba-endpoints-local.png` - los 10 endpoints probados en local

Pendientes - pantalla completa (las tomas tu con `Win+Shift+S`):

4. `04-vscode-proyecto.png` - VS Code con la carpeta del proyecto y `app.py` abierto.
5. `05-navegador-localhost-8080.png` - navegador en `http://localhost:8080`.
6. `06-aws-ec2.png` - consola AWS: la instancia EC2 Ubuntu "En ejecucion" y su Security Group (puerto 8080).
7. `07-dockerhub-repositorio.png` - el repositorio de la imagen en hub.docker.com.
8. `08-postman.png` - Postman contra `http://IP_PUBLICA_EC2:8080` (un GET y un POST/backup).

Pendientes - terminal (bash del EC2 o PowerShell local):

9. `09-dockerhub-tag-push.png` - `docker tag` y `docker push`.
10. `10-ec2-docker-pull-run.png` - por SSH en el EC2: `docker --version`, `docker pull`, `docker run`, `docker ps`.
11. `11-prueba-endpoints-ec2.png` - `python tests/smoke_test.py http://IP_PUBLICA_EC2:8080` (los 10 endpoints en el EC2).
