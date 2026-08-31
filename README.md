# Agentic LLM Serving Platform

A high-throughput, cost-efficient, caching-aware serving layer designed specifically for multi-agent LLM workflows. It serves as the intelligent bridge between client applications and underlying LLMs (like vLLM or Ollama), enforcing admission control, providing tenant-isolated caching, and abstracting the orchestration of complex AI tasks.

## 🚀 Key Features

*   **Bounded Admission Control:** Prevents system overload by shedding excess load (HTTP 503) instead of letting requests hang indefinitely in unbounded queues.
*   **Workload-Aware Routing:** Dynamically routes traffic based on the workload type (e.g., sending chat to vLLM, background batch jobs to local Ollama instances).
*   **Strict Tenant Isolation:** Exact-match semantic caching respects `tenant_scope` and `auth_scope`, guaranteeing cross-tenant data boundaries.
*   **Prefix-Caching Optimization:** Implements a deterministic Prompt Builder designed to maximize Prefix Caching hits on engines like vLLM.
*   **Agent Task Graph Orchestration:** Manages multi-step AI loops, handling fan-out (parallel steps) and safe cancellation without locking up inference threads.
*   **Cloud Native:** Fully containerized and orchestrated via Kubernetes (with Kustomize overlays for GCP and Local environments).

## 🏗️ Architecture

The monorepo contains several distinct modules:

*   **`apps/gateway`**: The FastAPI ingress service handling admission, caching, and routing.
*   **`apps/agent-worker`**: The orchestrator for complex multi-agent workflows (implementing a robust Task Graph).
*   **`packages/*`**: Shared libraries containing Contracts, Prompt-Engine hashing, and Retrieval (VectorDB) logic.
*   **`infra/*`**: Docker Compose and Kubernetes configurations for deployment.

For detailed architecture diagrams, refer to [Architecture Overview](docs/architecture/overview.md).

## 💻 Running Locally (Docker Compose)

The easiest way to start development is using Docker Compose. It spins up the Gateway, Redis, Qdrant (Vector DB), and Ollama.

1.  **Clone and prepare the environment:**
    ```bash
    cp .env.example .env
    ```
2.  **Start the Local Stack:**
    ```bash
    docker compose -f infra/compose/docker-compose.yml --profile local up -d --build
    ```
3.  **Access Services:**
    *   Gateway API: `http://localhost:8000/docs`
    *   Qdrant Dashboard: `http://localhost:6333/dashboard`

*(To run the full stack with the vLLM GPU engine, append `--profile gpu` to the compose command).*

## ☁️ Deploying to Kubernetes (GCP / Local)

The platform is designed to scale horizontally on Google Kubernetes Engine (GKE) or test locally via Docker Desktop Kubernetes using **Kustomize**.

Refer to the [Kubernetes Deployment Guide](docs/operations/kubernetes_guide.md) for step-by-step instructions on deploying the `local` or `gcp` overlays.

## 🛠️ Development

This monorepo uses `uv` for ultra-fast Python package management.

```bash
# Sync dependencies
uv sync

# Run tests
uv run pytest
```
