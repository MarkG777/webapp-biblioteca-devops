# Proyecto Integrador: Pipeline CI/CD

API REST **Biblioteca** (Flask + SQLite) empaquetada en Docker. Cada `git push` a `main` ejecuta pruebas, construye la imagen, la publica en Docker Hub y la despliega en una instancia EC2 de AWS.

Uso de herramientas de IA en el proyecto: ver [IA.md](IA.md).

## Arquitectura

```
git push a main
  -> GitHub Actions: pruebas (Jest) + build de la imagen
  -> Docker Hub: :latest y :<sha del commit>
  -> Deploy por SSH a EC2: pull, detener el contenedor viejo, ejecutar en el puerto 80
  -> Usuario: http://IP_EC2/api/...
```

| Archivo | Para qué sirve |
|---|---|
| `app.py` | API Flask con 12 endpoints y SQLite |
| `socket_server.py` | Servidor TCP en el puerto 6061 (protocolo `{insert:...}` y `{get:...}`) |
| `Dockerfile` | Imagen con Flask (gunicorn) y el socket |
| `.github/workflows/main.yml` | Pipeline de GitHub Actions |
| `tests/test_api.py`, `tests/test_socket_tcp.py` | Pruebas pytest de la API y del socket (cobertura minima 70%) |
| `tests/api.test.js` | Pruebas Jest: 10 endpoints x 3 escenarios |
| `tests/socket.test.js` | Pruebas Jest del socket TCP |
| `endpoints.http` | Pruebas manuales con la extensión REST Client de VS Code |
| `socket-demo.ps1` | Demo del socket desde PowerShell |

## Ejecutar en local

Requisitos: Docker, Node.js 22.

```bash
docker build -t webapp:latest .
docker run -d -p 8080:80 -p 6061:6061 --name webapp-container webapp:latest

npm ci
BASE_URL=http://localhost:8080 SOCKET_PORT=6061 npm test

pip install -r requirements-dev.txt
python -m pytest --cov=app --cov=socket_server --cov-report=term-missing --cov-fail-under=70
```

Para detener y borrar el contenedor: `docker rm -f webapp-container`.

## Configuración (GitHub Secrets)

El repositorio no contiene IPs, llaves ni tokens. Estos valores se guardan en **Settings > Secrets and variables > Actions**:

| Secreto | Contenido |
|---|---|
| `DOCKERHUB_USERNAME` | Usuario de Docker Hub |
| `DOCKERHUB_TOKEN` | Token de acceso (no la contraseña) |
| `EC2_HOST` | IP pública de la instancia EC2 |
| `EC2_SSH_KEY` | Contenido del archivo `.pem` de la instancia |

## Despliegue en EC2

1. Instancia Ubuntu Server (t3.micro) con Docker instalado.
2. Security Group: TCP 22 (SSH) y TCP 80 (HTTP), desde `0.0.0.0/0`.
3. Con el pipeline, el job `deploy` (solo en push a `main`) descarga `:latest`, reemplaza el contenedor y comprueba que la API responda en el puerto 80.

Para probar la API en la nube, cambia `localhost` por la IP pública en `endpoints.http`, o usa:

```bash
BASE_URL=http://IP_EC2 npm test
```

## Estado

| Parte | Estado |
|---|---|
| API con 12 endpoints y pruebas Jest (10 endpoints x 3 escenarios) | Hecho |
| Dockerfile y pruebas del socket | Hecho |
| Pipeline: pruebas, build y publicación en Docker Hub | Hecho |
| Cobertura de código con pytest-cov (mínimo 70%, actual 96%) | Hecho |
| Pipeline en pull requests y push, con cobertura en los logs | Hecho |
| Deploy por SSH en el puerto 80, verificado desde internet | Hecho |
