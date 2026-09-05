.PHONY: install test lint format format-check up down up-profiles-local up-profiles-gpu down-profiles logs validate-compose build-k8s download-loras

install:
	uv sync

test:
	uv run pytest -v

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

up:
	docker compose up -d --build

down:
	docker compose down

up-profiles-local:
	docker compose -f infra/compose/docker-compose.yml --profile local up -d --build

up-profiles-gpu:
	docker compose -f infra/compose/docker-compose.yml --profile local --profile gpu up -d --build

down-profiles:
	docker compose -f infra/compose/docker-compose.yml --profile local --profile gpu down

validate-compose:
	docker compose config
	docker compose -f infra/compose/docker-compose.yml config

logs:
	docker compose logs -f

build-k8s:
	docker build -t gateway:v1.2 -f apps/gateway/Dockerfile .
	docker build -t agent-worker:v1.2 -f apps/agent-worker/Dockerfile .
	docker build -t playground:v1.1 apps/playground

download-loras:
	python scripts/download_real_loras.py
