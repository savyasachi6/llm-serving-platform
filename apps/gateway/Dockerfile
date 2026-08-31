# Use a slim, official Python 3.12 image as the base to keep the image size small
# while ensuring we have the required Python runtime for the application.
FROM python:3.12-slim

# Set the working directory inside the container to /app
# All subsequent commands (COPY, RUN, CMD) will be executed in this directory.
WORKDIR /app

# Install 'uv', a fast Python package installer and resolver.
# This replaces standard pip for faster and more deterministic dependency resolution.
RUN pip install uv

# --- Dependency Resolution Stage ---
# We copy ONLY the pyproject.toml files first before copying the actual source code.
# This allows Docker to cache the dependency installation layer. If source code changes
# but dependencies don't, Docker reuses the cached dependencies layer, speeding up builds.

# Copy the root workspace configuration
COPY pyproject.toml .

# Copy the gateway application's specific project configuration
COPY apps/gateway/pyproject.toml apps/gateway/

# Copy the project configurations for all internal shared packages
# The gateway depends on these packages for contracts, prompt engineering, etc.
COPY packages/contracts/pyproject.toml packages/contracts/
COPY packages/common/pyproject.toml packages/common/
COPY packages/prompt-engine/pyproject.toml packages/prompt-engine/
COPY packages/retrieval/pyproject.toml packages/retrieval/
COPY packages/evaluation/pyproject.toml packages/evaluation/

# --- Source Code Stage ---
# Copy the actual application source code for the gateway.
COPY apps/gateway/app apps/gateway/app
# Copy the actual source code for all shared packages.
COPY packages packages

# Run 'uv sync' to install all dependencies specified in the pyproject.toml files.
# The '--no-dev' flag ensures we don't install development dependencies (like pytest) in the production image.
RUN uv sync --no-dev

# Expose port 8000 to tell Docker that the container listens on this network port at runtime.
# This doesn't actually publish the port to the host machine, it acts as documentation between the image builder and the person running the container.
EXPOSE 8000

# Define the default command to run when the container starts.
# We use 'uv run' to execute uvicorn within the managed virtual environment.
# 'apps.gateway.app.main:app' points to the FastAPI application instance.
# '--host 0.0.0.0' binds the server to all network interfaces so it can receive outside traffic.
# '--port 8000' specifies the listening port.
CMD ["uv", "run", "uvicorn", "apps.gateway.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
