# FastAPI JWT Auth

Production-oriented JWT authentication service built with FastAPI, PostgreSQL, and Redis.

Implements secure token-based authentication with access/refresh token rotation, Redis-backed revocation, and a fully async layered architecture designed for scalability and maintainability.

## What Is Implemented

- FastAPI app with versioned API prefix: `/api/v1`
- JWT authentication:
  - Access token in response body
  - Refresh token in `HttpOnly` cookie
- Refresh token rotation with one-time use semantics via Redis `GETDEL`
- Password hashing with Argon2 (Passlib)
- Async SQLAlchemy + asyncpg
- Alembic migration setup
- Centralized exception handling
- Basic rate limiting middleware (SlowAPI)
- CORS middleware configuration
- Automated CI/CD pipelines (GitHub Actions)

## Tech Stack

- Python
- FastAPI
- SQLAlchemy (async)
- PostgreSQL (asyncpg)
- Redis
- Alembic
- PyJWT
- Passlib (argon2)
- Pydantic Settings
- Ruff, Mypy, and Black (Linting & Formatting)
- GitHub Actions (CI/CD)

## Project Structure

```text
.
|- alembic/
|  |- env.py
|  |- versions/
|- app/
|  |- main.py
|  |- lifespan.py
|  |- api/
|  |  |- dependencies/
|  |  |- middlewares/
|  |  |- v1/
|  |  |  |- endpoints/
|  |- core/
|  |- crud/
|  |- db/
|  |- exceptions/
|  |- models/
|  |- schemas/
|  |- services/
|  |- utils/
|- tests/
|  |- fakes/
|  |- unit/
|- alembic.ini
|- pyproject.toml
|- poetry.lock
|- pytest.ini
|- .env.template
|- .env.docker
|- README.md
```

## Authentication Flow

1. Register a user (`POST /api/v1/register`)
2. Login (`POST /api/v1/login`)
3. Receive:
   - `access_token` in JSON response
   - `refresh_token` in secure `HttpOnly` cookie
4. Use access token for protected endpoints (Bearer auth)
5. Refresh access token (`POST /api/v1/refresh`) using refresh cookie
6. Logout (`POST /api/v1/logout`) revokes refresh token in Redis and clears cookie

## API Endpoints

Auth endpoints are under `/api/v1`. Health endpoints are top-level.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health/live` | No | Liveness probe |
| GET | `/health/ready` | No | Readiness probe (checks Postgres + Redis) |
| POST | `/api/v1/register` | No | Register new user |
| POST | `/api/v1/login` | No | Login with username/password form |
| POST | `/api/v1/refresh` | No | Rotate refresh token and issue new access token |
| POST | `/api/v1/logout` | No | Revoke current refresh token and clear cookie |
| GET | `/api/v1/about_me` | Bearer | Get current authenticated user |

## Quick Start (Poetry)

### 1. Prerequisites

- Python 3.12+
- Poetry 2.0+
- PostgreSQL
- Redis

### 2. Install Poetry

If you do not have Poetry installed:

```bash
pipx install poetry
```

### 3. Install dependencies

Runtime dependencies:

```bash
poetry install
```

Development and testing tools:

```bash
poetry install --with dev
```

Tip: you can run `poetry shell` once and then run commands without `poetry run`.

### 4. Configure environment

Create `.env` from template:

```bash
cp .env.template .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.template .env
```

Set the required variables:

| Variable | Required | Notes |
|---|---|---|
| `DEBUG` | No | `true` or `false` |
| `CORS_ORIGINS` | No | JSON array of allowed origins |
| `DATABASE_URL` | Yes | Must start with `postgresql+asyncpg://` or `postgres+asyncpg://` |
| `REDIS_URL` | Yes | Must start with `redis://` or `rediss://` |
| `ACCESS_SECRET` | Yes | Min length: 32 |
| `REFRESH_SECRET` | Yes | Min length: 32 |
| `ACCESS_TOKEN_EXPIRE_M` | No | Default: `15` |
| `REFRESH_TOKEN_EXPIRE_M` | No | Default: `43200` |
| `COOKIE_SECURE` | No | Default: `true` |
| `COOKIE_SAMESITE` | No | One of `lax`, `strict`, `none` |

Important for local HTTP development:

- If you test without HTTPS, set `COOKIE_SECURE=false`
- Otherwise browser/client may not send refresh cookie, and `/refresh`/`/logout` can fail with `401`

### 5. Run database migrations

```bash
poetry run alembic upgrade head
```

### 6. Start the app

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Quick Start (Docker Compose)

1. Update `.env.docker` with real secrets.
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
make up
make down
make migrate
make makemigrations m="describe change"
make logs
```

For production deployment (e.g., on a VPS), a dedicated compose file is provided:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

## Testing

Run all tests:

```bash
poetry run pytest
```

Run only unit tests:

```bash
poetry run pytest tests/unit
```

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

## Request Examples

### Register

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"john_doe","email":"john@example.com","password":"StrongPass123"}'
```

### Login (stores refresh cookie into file)

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  -d "username=john_doe&password=StrongPass123"
```

### Refresh

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/refresh" \
  -b cookies.txt \
  -c cookies.txt
```

### About Me

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/about_me" \
  -H "Authorization: Bearer <access_token>"
```

### Logout

```bash
curl -i -X POST "http://127.0.0.1:8000/api/v1/logout" \
  -b cookies.txt \
  -c cookies.txt
```

## Error Model

Application-specific errors use this shape:

```json
{"detail": "..."}
```

Common statuses:

- `201` Created (register)
- `200` OK (login, refresh, logout, about_me)
- `401` Unauthorized (invalid credentials/token)
- `404` Not Found (user not found)
- `409` Conflict (user already exists)
- `429` Too Many Requests (rate limit exceeded)

## Migrations

Create migration:

```bash
poetry run alembic revision --autogenerate -m "describe change"
```

Upgrade DB:

```bash
poetry run alembic upgrade head
```

Downgrade one revision:

```bash
poetry run alembic downgrade -1
```

## Current Limitations

- No email verification flow
- No password reset flow
- No role-based authorization checks (role field exists but is not enforced)
- Test coverage is unit-focused; no integration tests yet