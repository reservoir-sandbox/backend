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
  - Validation of ELF magic bytes `\x7fELF`
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
   - Magic bytes = `\x7fELF` (ELF binary)
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

### Overview

| Method | Path                          | Auth             | Description                                        |
|--------|-------------------------------|------------------|----------------------------------------------------|
| GET    | `/health/live`                | No               | Liveness probe                                     |
| GET    | `/health/ready`               | No               | Readiness probe (checks PostgreSQL + Redis)        |
| POST   | `/api/v1/register`            | No               | Register new user                                  |
| POST   | `/api/v1/login`               | No               | Login (username/password form)                     |
| POST   | `/api/v1/refresh`             | No               | Rotate refresh token, issue new access token       |
| POST   | `/api/v1/logout`              | No               | Revoke refresh token, clear cookie                 |
| GET    | `/api/v1/about_me`            | Bearer           | Get current user profile                           |
| GET    | `/api/v1/samples`             | Bearer           | List all samples owned by current user             |
| POST   | `/api/v1/samples`             | Bearer           | Upload an ELF binary for analysis                  |
| DELETE | `/api/v1/samples/{id}`        | Bearer           | Delete a user-sample link (remove ownership)       |
| GET    | `/api/v1/jobs/{id}`           | Bearer           | Get job details (with tasks) by job ID             |

---

### Endpoint Details

---

#### `GET /health/live`

Simple liveness check. No authentication required.

**Example request:**
```bash
curl -X GET "http://127.0.0.1:8000/health/live"
```

**Example response (200 OK):**
```json
{
  "status": "ok"
}
```

---

#### `GET /health/ready`

Readiness probe. Verifies connectivity to PostgreSQL and Redis.

**Example request:**
```bash
curl -X GET "http://127.0.0.1:8000/health/ready"
```

**Example response (200 OK):**
```json
{
  "status": "ok",
  "services": {
    "postgres": "ok",
    "redis": "ok"
  }
}
```

**Example response (503 Service Unavailable) when a service is down:**
```json
{
  "status": "error",
  "services": {
    "postgres": "error",
    "redis": "ok"
  }
}
```

---

#### `POST /api/v1/register`

Create a new user account.

**Request body** — JSON (`UserRegister` schema):
| Field    | Type     | Constraints   | Description     |
|----------|----------|---------------|-----------------|
| username | string   | 4–24 chars    | Lowercased automatically |
| email    | string   | Valid email   | User's email address |
| password | string   | 8–24 chars    | Plain-text password (hashed with Argon2) |

**Example request:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"StrongPass123"}'
```

**Example response (201 Created):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "role": "user",
  "created_at": "2025-03-28T12:00:00",
  "updated_at": "2025-03-28T12:00:00"
}
```

**Possible errors:**  
- `409 Conflict` — username or email already exists.

---

#### `POST /api/v1/login`

Authenticate with username and password using `application/x-www-form-urlencoded` (standard OAuth2 password flow).

Sets an `HttpOnly` cookie named `refresh_token` and returns an access token in the response body.

**Request body** — form data:
| Field    | Type   | Description        |
|----------|--------|--------------------|
| username | string | User's username    |
| password | string | User's password    |

**Example request:**
```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d "username=john_doe&password=StrongPass123"
```

**Example response (200 OK) — Headers will include `Set-Cookie` with the refresh token:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Possible errors:**  
- `401 Unauthorized` — invalid credentials.

---

#### `POST /api/v1/refresh`

Exchange a valid refresh token (from cookie) for a new access/refresh pair. Requires the `refresh_token` cookie to be present. The old refresh token is invalidated (one-time use).

**Example request (cookie from previous login):**
```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/refresh" \
  -b cookies.txt -c cookies.txt
```

**Example response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Possible errors:**  
- `401 Unauthorized` — missing, expired, or invalid refresh token.

---

#### `POST /api/v1/logout`

Revoke the current refresh token from Redis and clear the `refresh_token` cookie.

**Example request:**
```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/logout" \
  -b cookies.txt -c cookies.txt
```

**Example response (200 OK):**
```json
{
  "message": "logout successfully!"
}
```

---

#### `GET /api/v1/about_me`

Get the profile of the currently authenticated user.

**Headers:** `Authorization: Bearer <access_token>`

**Example request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/about_me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example response (200 OK):**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "role": "user",
  "created_at": "2025-03-28T12:00:00",
  "updated_at": "2025-03-28T12:00:00"
}
```

**Possible errors:**  
- `401 Unauthorized` — missing or invalid token.

---

#### `GET /api/v1/samples`

List all samples owned by the current user. Returns an array of `SampleListItem` objects.

**Headers:** `Authorization: Bearer <access_token>`

**Example request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/samples" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example response (200 OK):**
```json
[
  {
    "sample_id": 1,
    "filename": "malware.elf",
    "uploaded_at": "2025-03-28T12:05:00",
    "latest_job_id": 1,
    "latest_job_status": "pending"
  },
  {
    "sample_id": 2,
    "filename": "benign.elf",
    "uploaded_at": "2025-03-28T12:10:00",
    "latest_job_id": 2,
    "latest_job_status": "completed"
  }
]
```

**Possible errors:**  
- `401 Unauthorized` — missing or invalid token.

---

#### `POST /api/v1/samples`

Upload an ELF binary for analysis. The file is validated for ELF magic bytes, deduplicated by SHA256, and stored in S3. A new Job with three tasks is created if the sample is new; otherwise an existing Job may be returned.

**Headers:** `Authorization: Bearer <access_token>`  
**Body:** `multipart/form-data` with field name `sample`

**Example request:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/samples" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -F "sample=@/path/to/malware.elf"
```

**Example response (201 Created):**
```json
{
  "id": 1,
  "sample_id": 1,
  "status": "pending",
  "created_at": "2025-03-28T12:15:00",
  "started_at": null,
  "finished_at": null
}
```

**Possible errors:**  
- `400 Bad Request` — file is not ELF (magic bytes mismatch).  
- `413 Payload Too Large` — file exceeds 10 MB.  
- `401 Unauthorized` — missing or invalid token.

---

#### `DELETE /api/v1/samples/{id}`

Delete the link between the current user and a sample (remove ownership). The sample itself (S3 object + DB record) is **not** removed.

**Headers:** `Authorization: Bearer <access_token>`  
**Path parameter:** `id` — integer, the `sample_id` from the list.

**Example request:**
```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/samples/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example response (204 No Content):** — empty body.

**Possible errors:**  
- `404 Not Found` — sample does not exist or does not belong to this user.  
- `401 Unauthorized` — missing or invalid token.

---

#### `GET /api/v1/jobs/{id}`

Get detailed information about a specific job, including its tasks (`JobTaskRead` list).

**Headers:** `Authorization: Bearer <access_token>`  
**Path parameter:** `id` — integer, the job ID.

**Example request:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/jobs/1" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Example response (200 OK):**
```json
{
  "id": 1,
  "sample_id": 1,
  "status": "pending",
  "created_at": "2025-03-28T12:15:00",
  "started_at": null,
  "finished_at": null,
  "tasks": [
    {
      "id": 1,
      "job_id": 1,
      "task_type": "STATIC",
      "status": "pending",
      "created_at": "2025-03-28T12:15:00",
      "started_at": null,
      "finished_at": null,
      "error": null
    },
    {
      "id": 2,
      "job_id": 1,
      "task_type": "SANDBOX",
      "status": "pending",
      "created_at": "2025-03-28T12:15:00",
      "started_at": null,
      "finished_at": null,
      "error": null
    },
    {
      "id": 3,
      "job_id": 1,
      "task_type": "ML",
      "status": "pending",
      "created_at": "2025-03-28T12:15:00",
      "started_at": null,
      "finished_at": null,
      "error": null
    }
  ]
}
```

**Possible errors:**  
- `404 Not Found` — job does not exist or does not belong to this user.  
- `401 Unauthorized` — missing or invalid token.

---

## Error Model

All application-specific errors return a JSON body with `{"detail": "..."}`.

### Common HTTP status codes

| Status | Error                          | Description                                |
|--------|--------------------------------|--------------------------------------------|
| 200    | OK                             | Successful operation                       |
| 201    | Created                        | Resource created (register, upload sample) |
| 204    | No Content                     | Resource deleted successfully              |
| 400    | Bad Request                    | Invalid file format (non-ELF)              |
| 401    | Unauthorized                   | Invalid credentials / expired or invalid token |
| 403    | Forbidden                      | Access denied (insufficient role)          |
| 404    | Not Found                      | User not found or resource not found       |
| 409    | Conflict                       | User already exists                        |
| 413    | Payload Too Large              | File exceeds maximum size (10 MB)          |
| 429    | Too Many Requests              | Rate limit exceeded                        |
| 500    | Internal Server Error          | Unexpected server error                    |

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