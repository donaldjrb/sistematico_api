# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Evitar archivos .pyc y forzar logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# ── Dependencias primero (mejor caché) ────────────────────────
COPY requirements*.txt ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r requirements-dev.txt

# ── Código ────────────────────────────────────────────────────
COPY . .

EXPOSE 8000

# Gunicorn con worker uvicorn
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "2", "-b", "0.0.0.0:8000", "app.main:app"]
