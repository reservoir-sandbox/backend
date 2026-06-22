# Reservoir

Backend service for automated Linux malware analysis.

Reservoir allows users to upload ELF binaries, stores samples in S3-compatible storage, manages analysis jobs and tasks, and provides secure JWT-based authentication. The project serves as the backend foundation for a scalable malware analysis platform where future workers will perform static analysis, sandbox execution, and machine-learning-based classification.

> **Status: active development** — the core backend infrastructure is implemented, including authentication, sample upload, job orchestration, PostgreSQL/Redis integration, S3 storage, health checks, CI/CD, and Docker deployment. Analysis workers (STATIC, SANDBOX, ML) are planned and their data models are already implemented.

## Architecture Overview

```text
User
 │
 ▼
FastAPI Backend
 │
 ├── Authentication (JWT + Redis)
 ├── Sample Upload (ELF validation)
 ├── Job Orchestration
 ├── Task Management
 │
 ├── PostgreSQL
 ├── Redis
 └── S3 Storage
```

## Key Features

* JWT authentication with refresh token rotation
* ELF binary upload and validation
* SHA256-based sample deduplication
* S3-compatible object storage integration
* Job and task orchestration system
* PostgreSQL and Redis integration
* Health checks and readiness probes
* Docker and Docker Compose deployment
* CI pipeline with Black, Ruff, Mypy, and Pytest
* Fully asynchronous architecture based on FastAPI and SQLAlchemy 2.x

## What Is Implemented

- FastAPI application with versioned API prefix `/api/v1`
- JWT authentication with access/refresh token rotation:
  - Access token in response body (15 min)
  - Refresh token in `HttpOnly` cookie (30 days)
  - Refresh token rotation with one-time-use semantics via Redis `GETDEL`
- Password hashing with Argon2 (Passlib)
- Async SQLAlchemy + asyncpg
- Alembic migration setup
- Centralized exception handling + HTTP exception mapping
- Rate limiting middleware (SlowAPI, configurable)
- CORS middleware
- Health checks: liveness (`/health/live`) and readiness (`/health/ready`) probing PostgreSQL and Redis
- **Sample (ELF binary) upload**:
  - Validation of ELF magic bytes `\\x7fELF`
  - File size limit (10 MB)
  - SHA256 deduplication
  - Upload to S3-compatible storage (MinIO / AWS S3)
  - Store sample metadata in PostgreSQL (size, sha256, object_name)
  - Track user ownership via `user_samples` join table
- **Job and Task management**:
  - On upload, creates a `Job` (status: pending) and three `JobTask` instances (STATIC, SANDBOX, ML)
  - Each task has its own status lifecycle (pending → running → completed/failed)
  - Job keeps started_at/finished_at timestamps
- S3 storage abstraction using `aiobotocore` (async S3 client)
- Redis-backed refresh token
- GitHub Actions CI: black, ruff, mypy, pytest
- Unit tests for `AuthService` and `UserService` with fake CRUD implementations
- Production-grade Dockerfile (multi-stage build, non-root user, healthcheck)
- Docker Compose files for development and production

## Tech Stack

| Component              | Technology                                      |
|------------------------|--------------------------------------------------|
| Language               | Python 3.12+                                     |
| Framework              | FastAPI 0.136+                                   |
| Database ORM           | SQLAlchemy 2.x (async) + asyncpg                 |
| Database               | PostgreSQL 16                                    |
| Cache / Token store    | Redis 7 (redis-py async)                         |
| Object storage         | S3-compatible (MinIO / AWS S3 via aiobotocore)   |
| Authentication         | JWT (HS256) with httpOnly cookie                 |
| Password hashing       | Argon2 (passlib)                                 |
| Schema validation      | Pydantic v2 (settings, models, validation)       |
| Migrations             | Alembic                                          |
| Rate limiting          | SlowAPI                                          |
| Testing                | pytest, pytest-asyncio, fakeredis, httpx         |
| Linting & Formatting   | Black, Ruff, Mypy                                |
| CI/CD                  | GitHub Actions                                   |
| Containerization       | Docker, Docker Compose                           |

## Project Structure

```text
app/
├── api/            # HTTP layer
├── services/       # Business logic
├── crud/           # Data access layer
├── models/         # Database models
├── schemas/        # API schemas
├── auth/           # Authentication & authorization
├── db/             # PostgreSQL, Redis, S3
├── dependencies/   # Dependency injection
├── core/           # Config, security, logging
└── utils/          # Shared helpers

tests/              # Unit tests
alembic/            # Database migrations
```

## Authentication Flow

1. **Register** (`POST /api/v1/register`) — creates a new user account (username, email, password). Password is hashed with Argon2 before storage.
2. **Login** (`POST /api/v1/login`) — validates credentials, returns `access_token` in JSON body and sets `refresh_token` in an `HttpOnly` cookie. The refresh token's JTI is stored in Redis (with TTL equal to its lifetime).
3. **Access protected endpoints** — use `Authorization: Bearer <access_token>` header. The token contains `sub` (user ID), `role`, and `type` ("access").
4. **Refresh** (`POST /api/v1/refresh`) — when access token expires, use the `refresh_token` cookie to obtain a new pair. The old refresh token is consumed (one-time use) via Redis `GETDEL`, and a new `refresh_token` is issued.
5. **Logout** (`POST /api/v1/logout`) — revokes the current refresh token (deletes from Redis) and clears the cookie.

### Token details

| Token           | Location       | Lifetime        | Contains                                 |
|-----------------|----------------|-----------------|------------------------------------------|
| `access_token`  | Response body  | 15 minutes (default) | `sub`, `role`, `type`, `exp`, `iat`, `jti` |
| `refresh_token` | HttpOnly cookie| 30 days (default)    | `sub`, `type`, `exp`, `iat`, `jti` |

## Sample Upload & Analysis Pipeline Flow

1. **User uploads a file** (`POST /api/v1/samples`, multipart, requires Bearer token)
2. **Validation** — checks:
   - File size ≤ 10 MB
   - Magic bytes = `\\x7fELF` (ELF binary)
3. **SHA256 hash** of file content is computed
4. **Deduplication** — checks if sample with same SHA256 already exists in database
   - If **exists**:
     - Checks if this user already owns a link to this sample (via `user_samples` table). If not, creates a new `UserSample` record.
     - If there is a **recent (pending/running/completed) job** for that sample, returns that job (avoids duplicate analysis).
     - Otherwise, creates a new `Job` for the existing sample.
   - If **not exists**:
     - Uploads file to S3 bucket with key `uploads/{sha256}`
     - Creates `Sample` record in PostgreSQL
     - Creates `UserSample` record
     - Creates a new `Job` with three `JobTask` records (STATIC, SANDBOX, ML)
5. **Response** returns the `Job` object with its current status (`pending`) and related timestamps.

### Job / Task model

- **Job** — represents one analysis run for a sample. Status lifecycle: `pending` → `running` → `completed` / `failed`.
- **JobTask** — individual analysis step within a job. Types: `STATIC`, `SANDBOX`, `ML`. Each task has its own status, start/end times, and optional error message.
- Currently, no workers are implemented to process these tasks — this is the next major development step.

## API Endpoints

| Method | Path                    | Auth             | Description                                      |
|--------|------------------------|------------------|--------------------------------------------------|
| GET    | `/health/live`         | No               | Liveness probe                                   |
| GET    | `/health/ready`        | No               | Readiness probe (checks PostgreSQL + Redis)      |
| POST   | `/api/v1/register`     | No               | Register new user                                |
| POST   | `/api/v1/login`        | No               | Login (username/password form)                   |
| POST   | `/api/v1/refresh`      | No               | Rotate refresh token, issue new access token     |
| POST   | `/api/v1/logout`       | No               | Revoke refresh token, clear cookie               |
| GET    | `/api/v1/about_me`     | Bearer           | Get current user profile                         |
| POST   | `/api/v1/samples`      | Bearer           | Upload an ELF binary for analysis                |

Full OpenAPI documentation is available at `http://localhost:8000/docs` after startup.

## Quick Start (Poetry)

### 1. Prerequisites

- Python 3.12+
- Poetry 2.0+
- PostgreSQL 16 running
- Redis 7 running
- S3-compatible storage (e.g., MinIO, AWS S3)

### 2. Install Poetry

```bash
pipx install poetry
```

### 3. Install dependencies

```bash
poetry install --with dev
```

### 4. Configure environment

```bash
cp .env.template .env
```

Edit `.env` with your configuration. Minimum required variables:

| Variable                | Required | Description                              |
|------------------------|----------|------------------------------------------|
| `DATABASE_URL`          | Yes      | `postgresql+asyncpg://user:pass@host:5432/dbname` |
| `REDIS_URL`             | Yes      | `redis://host:6379/0` or `rediss://...`  |
| `ACCESS_SECRET`         | Yes      | Min 32 chars, used to sign access tokens |
| `REFRESH_SECRET`        | Yes      | Min 32 chars, used to sign refresh tokens |
| `S3_ACCESS_KEY`         | Yes      | S3 access key                            |
| `S3_SECRET_KEY`         | Yes      | S3 secret key                            |
| `S3_ENDPOINT_URL`       | Yes      | S3 endpoint (e.g., `http://localhost:9000` for MinIO) |
| `S3_BUCKET_NAME`        | Yes      | S3 bucket name                           |

Optional variables: `DEBUG`, `CORS_ORIGINS`, `ACCESS_TOKEN_EXPIRE_M`, `REFRESH_TOKEN_EXPIRE_M`, `COOKIE_SECURE`, `COOKIE_SAMESITE`.

> **Note for local HTTP testing:** Set `COOKIE_SECURE=false` in `.env`; otherwise browsers may refuse to send the `HttpOnly` cookie over HTTP.

### 5. Run database migrations

```bash
poetry run alembic upgrade head
```

### 6. Start the app

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger UI: `http://127.0.0.1:8000/docs`  \
ReDoc: `http://127.0.0.1:8000/redoc`

## Quick Start (Docker Compose)

### Development

1. Update `.env.docker` with real secrets (see environment variables above).
2. Start services:

```bash
docker compose up --build
```

3. Run migrations:

```bash
docker compose run --rm app alembic upgrade head
```

Makefile shortcuts:

```bash
make up                  # docker compose up --build
make down                # docker compose down
make migrate             # run migrations
make makemigrations m="message"  # create new migration
make logs                # follow logs
```

### Production

For production deployment (e.g., on a VPS), use the provided production compose file:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This compose expects a pre-built image from GitHub Container Registry and a properly filled `.env` file.

## Request Examples

### Register

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"StrongPass123"}'
```

### Login (stores refresh cookie)

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d "username=john_doe&password=StrongPass123"
```

Save the access_token from the response for subsequent requests.

### Refresh

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/refresh" \
  -b cookies.txt -c cookies.txt
```

### About Me

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/about_me" \
  -H "Authorization: Bearer <access_token>"
```

### Upload Sample (ELF binary)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/samples" \
  -H "Authorization: Bearer <access_token>" \
  -F "sample=@/path/to/malware.elf"
```

### Logout

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/logout" \
  -b cookies.txt -c cookies.txt
```

## Error Model

All application-specific errors return a JSON body with `{"detail": "..."}`.

### Common HTTP status codes

| Status | Error                          | Description                                |
|--------|--------------------------------|--------------------------------------------|
| 200    | OK                             | Successful operation                       |
| 201    | Created                        | Resource created (register, upload sample) |
| 400    | Bad Request                    | Invalid file format (non-ELF)              |
| 401    | Unauthorized                   | Invalid credentials / expired or invalid token |
| 403    | Forbidden                      | Access denied (insufficient role)          |
| 404    | Not Found                      | User not found                             |
| 409    | Conflict                       | User already exists                        |
| 413    | Payload Too Large              | File exceeds maximum size (10 MB)          |
| 429    | Too Many Requests              | Rate limit exceeded                        |
| 500    | Internal Server Error          | Unexpected server error                    |

## Testing

Run all tests:

```bash
poetry run pytest
```

Run only unit tests:

```bash
poetry run pytest tests/unit
```

Run with coverage (if `coverage` is installed):

```bash
poetry run coverage run -m pytest && poetry run coverage report
```

The test suite uses **fake implementations** (e.g., `FakeUserCRUD`) to avoid external dependencies, and `fakeredis` for Redis mocking.

## Development Tools

Format code with Black:

```bash
poetry run black .
```

Lint code with Ruff:

```bash
poetry run ruff check .
```

Check types with Mypy:

```bash
poetry run mypy app
```

## Migrations

Create a new migration:

```bash
poetry run alembic revision --autogenerate -m "describe change"
```

Upgrade to latest:

```bash
poetry run alembic upgrade head
```

Downgrade one revision:

```bash
poetry run alembic downgrade -1
```

## Current Limitations

- **No monitoring stack** — Prometheus, Grafana, ELK are not deployed in the current codebase.
- **Test coverage** — currently covers only `AuthService` and `UserService`; `SampleService`, `JobService`, `StorageService` lack tests.

## Future Plans

- [ ] Implement **analysis workers** (STATIC, SANDBOX, ML) as separate services/pods in Kubernetes
- [ ] **Static analysis** — YARA rules scanning, readelf output parsing, strings extraction, import table inspection
- [ ] **ML classification** — model for ELF family detection and maliciousness scoring
- [ ] **Sandbox execution** — gVisor containers with network isolation (no outbound traffic), behavioral logging
- [ ] **Report generation** — structured reports combining all analysis results
- [ ] **Monitoring integration** — Prometheus metrics, Grafana dashboards, ELK log aggregation
- [ ] **Web frontend** — user-friendly dashboard for submitting samples and viewing reports

## License

MIT

## Author

Rushan Shafeev — [GitHub](https://github.com/Lntck)