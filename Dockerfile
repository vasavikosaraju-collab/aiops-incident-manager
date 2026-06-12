# --- Base image -------------------------------------------------------------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System dependencies required to build psycopg2 (PostgreSQL client) and
# run a minimal Django/ASGI stack.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Python dependencies -----------------------------------------------------
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Application code --------------------------------------------------------
COPY backend /app/backend
COPY model_training /app/model_training

WORKDIR /app/backend

EXPOSE 8000

# Run database migrations, then start the ASGI server (daphne) so both
# regular HTTP requests and the /ws/notifications/ WebSocket route are
# served from a single process. In a real AWS ECS deployment this is the
# container's entrypoint; the ECS service definition adds environment
# variables for RDS/Redis (see README "AWS Deployment" section).
CMD ["sh", "-c", "python manage.py migrate --noinput && daphne -b 0.0.0.0 -p 8000 aiops.asgi:application"]
