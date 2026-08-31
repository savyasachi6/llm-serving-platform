# Agentic LLM Serving Platform

A high-throughput, cost-efficient, caching-aware serving layer designed specifically for multi-agent LLM workflows. It serves as the intelligent bridge between client applications and underlying LLMs (like vLLM or Ollama), enforcing admission control, providing tenant-isolated caching, and abstracting the orchestration of complex AI tasks.

## 🚀 Key Features

*   **Bounded Admission Control:** Prevents system overload by shedding excess load (HTTP 503) instead of letting requests hang indefinitely in unbounded queues.
*   **Heterogeneous Workload Routing:** Dynamically routes traffic based on workload type (e.g., routing complex reasoning to an 8-bit Gemma model, and high-volume text transformations to a 4-bit Llama model).
*   **Multi-LoRA Dynamic Hot-Swapping:** A single vLLM instance serves multiple fine-tuned models (LoRA adapters) simultaneously on the same base model. The `triage` and `redactor` agents dynamically request specialized LoRAs (`reasoning` and `reflection`) at runtime, and vLLM hot-swaps them in milliseconds.
*   **Micro-Agent Assembly Line:** Discards brittle "Genius Agent" patterns in favor of single-shot, hyper-focused micro-agents (Triage, Redact, Respond) that scale flawlessly on smaller 2B-3B models.
*   **Strict Tenant Isolation:** Exact-match semantic caching respects `tenant_scope` and `auth_scope`, guaranteeing cross-tenant data boundaries.
*   **Prefix-Caching Optimization:** Implements a deterministic Prompt Builder designed to maximize Prefix Caching hits on engines like vLLM.
*   **Cloud Native (GPU Time-Slicing):** Fully containerized and orchestrated via Kubernetes. Utilizes NVIDIA GPU Time-slicing to share a single physical GPU across multiple heterogeneous model nodes locally.

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
