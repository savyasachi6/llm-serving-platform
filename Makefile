.PHONY: install test lint format up down logs

install:
	uv sync

test:
	uv run pytest -q

lint:
	uv run ruff check .

format:
	uv run ruff format .

up:
	docker compose --profile gpu --profile local up -d --build

down:
	docker compose --profile gpu --profile local down

logs:
	docker compose logs -f
