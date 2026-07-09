# --- Stage 1: Builder stage ---
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Export requirements and install dependencies into a dedicated prefix folder
RUN poetry export --without-hashes --format=requirements.txt --output /tmp/requirements.txt \
    && pip install --no-cache-dir \
        --prefix=/install \
        --ignore-installed \
        -r /tmp/requirements.txt


# --- Stage 2: Production runtime stage ---
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a secure non-root system user and group
RUN addgroup --system fastapi && \
    adduser --system --ingroup fastapi fastapi

WORKDIR /app

# Copy installed python packages directly from the builder stage
COPY --from=builder /install /usr/local

# Copy ONLY the required application production source code (prevents copying .git, tests, etc.)
COPY ./app ./app

COPY ./alembic.ini ./alembic.ini

COPY ./alembic ./alembic

# Adjust filesystem ownership to the non-root execution user
RUN chown -R fastapi:fastapi /app

USER fastapi

# CRITICAL FIX: Port changed to 8080 to perfectly match your Kubernetes service values
EXPOSE 8080

# Note: We removed the inline Docker HEALTHCHECK.
# Probes will be fully managed at the Kubernetes pod level via Flux deployment.

# Start FastAPI application using uvicorn server on port 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
