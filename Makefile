up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose run --rm app alembic upgrade head

makemigrations:
	docker compose run --rm app alembic revision --autogenerate -m "$(m)"

logs:
	docker compose logs -f