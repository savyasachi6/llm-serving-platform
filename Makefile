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

build-k8s:
	docker build -t gateway:v1.2 -f apps/gateway/Dockerfile .
	docker build -t agent-worker:v1.2 -f apps/agent-worker/Dockerfile .
	docker build -t playground:v1.1 apps/playground
