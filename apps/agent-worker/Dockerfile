# Base image: We use a slim version of Python 3.12.
# 'slim' means it only contains the minimal packages needed to run Python,
# which helps reduce the overall Docker image size, leading to faster pulls and smaller footprint.
FROM python:3.12-slim

# WORKDIR sets the default directory for the container.
# Any RUN, CMD, ADD, or COPY instructions that follow will be executed in this directory.
# Creating a dedicated /app directory is a best practice to avoid cluttering the root filesystem.
WORKDIR /app

# Install 'uv', a fast, Rust-based Python package manager and resolver.
# We use this instead of the default 'pip' because it significantly speeds up dependency installation
# and ensures reproducible virtual environments.
RUN pip install uv

# --- Dependency Layer Caching ---
# We deliberately copy the pyproject.toml files (which list dependencies) BEFORE copying the source code.
# Docker caches layers; if the source code changes but dependencies don't, Docker will skip reinstalling
# dependencies and just use the cached layer, which speeds up the build process dramatically.

# Copy the root workspace configuration for uv.
COPY pyproject.toml .

# Copy the agent-worker application's specific configuration.
COPY apps/agent-worker/pyproject.toml apps/agent-worker/

# Copy the configurations for all internal shared packages (monorepo structure).
# The agent worker depends on these common libraries to function.
COPY packages/contracts/pyproject.toml packages/contracts/
COPY packages/common/pyproject.toml packages/common/
COPY packages/prompt-engine/pyproject.toml packages/prompt-engine/
COPY packages/retrieval/pyproject.toml packages/retrieval/
COPY packages/evaluation/pyproject.toml packages/evaluation/

# --- Source Code Layer ---
# Now we copy the actual application source code into the container.
COPY apps/agent-worker/app apps/agent-worker/app
# Copy the source code for the internal shared packages.
COPY packages packages

# Run 'uv sync' to resolve and install all dependencies defined in the pyproject.toml files.
# The '--no-dev' flag instructs uv to skip installing development tools (like test frameworks, linters)
# to keep the production image as small and secure as possible.
RUN uv sync --no-dev

# Set PYTHONPATH to include apps/agent-worker and all packages
ENV PYTHONPATH="/app/apps/agent-worker:/app/packages/contracts/src:/app/packages/common/src:/app/packages/prompt-engine/src:/app/packages/retrieval/src:/app/packages/evaluation/src"

# EXPOSE acts as documentation to inform Docker that this container listens on port 8001 at runtime.
# This does not automatically publish the port to the outside world; that is handled by Kubernetes or Docker Compose.
EXPOSE 8001

# The CMD instruction defines the default command executed when the container starts.
# - 'uv run' ensures the command runs within the workspace virtual environment.
# - 'uvicorn' is an ASGI web server implementation for Python.
# - '--app-dir apps/agent-worker' tells uvicorn where to find the application package.
# - 'app.server:app' points to the FastAPI application instance.
# - '--host 0.0.0.0' binds the server to all network interfaces, allowing external traffic (like from the Gateway) to reach it.
# - '--port 8001' sets the listening port.
CMD ["uv", "run", "uvicorn", "app.server:app", "--app-dir", "apps/agent-worker", "--host", "0.0.0.0", "--port", "8001"]
