FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy pyproject configuration
COPY pyproject.toml .
COPY apps/gateway/pyproject.toml apps/gateway/
COPY packages/contracts/pyproject.toml packages/contracts/
COPY packages/common/pyproject.toml packages/common/
COPY packages/prompt-engine/pyproject.toml packages/prompt-engine/
COPY packages/retrieval/pyproject.toml packages/retrieval/
COPY packages/evaluation/pyproject.toml packages/evaluation/

# Copy source code
COPY apps/gateway/app apps/gateway/app
COPY packages packages

# Sync dependencies using uv
RUN uv sync --no-dev

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run", "uvicorn", "apps.gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
