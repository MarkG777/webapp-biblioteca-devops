FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DB_PATH=/app/data/biblioteca.db \
    BACKUP_DIR=/app/backups

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY socket_server.py .

RUN mkdir -p /app/data /app/backups

EXPOSE 80
EXPOSE 6061

CMD ["sh", "-c", "python socket_server.py & exec gunicorn --bind 0.0.0.0:80 --workers 2 app:app"]
