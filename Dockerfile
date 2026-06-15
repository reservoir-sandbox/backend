# Builder stage
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 POETRY_VERSION=2.3.4

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && poetry self add poetry-plugin-export

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN poetry export \
    --only main \
    --without-hashes \
    --format=requirements.txt \
    --output /tmp/requirements.txt \
    && pip install --no-cache-dir \
        --prefix=/install \
        --ignore-installed \
        -r /tmp/requirements.txt


# Runtime stage
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system fastapi && \
    adduser --system --ingroup fastapi fastapi

WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

RUN chown -R fastapi:fastapi /app

USER fastapi

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]