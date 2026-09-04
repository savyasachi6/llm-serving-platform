# Cost-Efficient LLM Serving Platform

## 🎯 Project Purpose
This repository provides a high-throughput, cost-efficient, caching-aware serving layer designed specifically for multi-agent LLM workflows. It serves as the intelligent bridge between client applications and underlying LLMs (like vLLM or Ollama).

## 💡 What Problem This Solves
Running multi-agent AI systems often leads to massive token overhead and GPU memory exhaustion. Standard architectures fail when multiple agents request overlapping context simultaneously. This system solves that by enforcing admission control, providing tenant-isolated caching, and abstracting the orchestration of complex AI tasks using a unique `kvcached` IPC memory-sharing daemon and dynamic LoRA hot-swapping.

## 🏗️ High-Level Architecture Summary
The system consists of an API Gateway, an Agent Worker for orchestration, a React frontend, a Redis cache, and two vLLM inference engines (`vllm-responder` and `vllm-agents`). A sidecar daemon called `kvcached` manages GPU memory pooling.

### How the System Works
1. **Client Request**: A user submits a prompt via the Frontend or Gateway.
2. **Gateway**: Checks Redis for an exact-match semantic cache (respecting tenant isolation). If a miss, routes to Agent Worker.
3. **Agent Worker**: Orchestrates a pipeline: Triage -> Redact -> Respond.
4. **kvcached Daemon**: Pre-allocates GPU VRAM and shares it via a Unix socket `/tmp/kvcached-ipc/kvcached.sock`.
5. **vLLM Engines**: Request memory from `kvcached`. `vllm-agents` hot-swaps LoRAs for Triage/Redact. `vllm-responder` generates the final output.

## 🖼️ Visual Architecture Diagram

```mermaid
flowchart LR
    User[User / Client] -->|HTTPS Request| Ingress[Ingress / Load Balancer]
    Ingress --> Gateway[Gateway Service]
    Gateway --> Redis[(Redis Cache)]
    Gateway --> Worker[Agent Worker Service]
    Worker --> VLLM_A[vllm-agents (Triage/Redact)]
    Worker --> VLLM_R[vllm-responder (Final)]
    VLLM_A -.-> |IPC Socket| KVC[kvcached Daemon]
    VLLM_R -.-> |IPC Socket| KVC
```

## 🚀 Quick-Start Instructions

### Prerequisites
- Docker & Docker Compose
- NVIDIA GPU (if running full vLLM engines)
- Linux / WSL2 (for GPU support)

### Local Development Path
1. Copy the environment file: `cp .env.example .env`
2. Start the mock backend for fast dev: `USE_MOCK=True docker compose up -d`
3. Access Gateway at `http://localhost:8000/docs`

### Docker & Docker Compose Path
To run the full multi-engine pipeline locally using Docker Compose:
```bash
docker compose -f docker-compose.yml up -d --build
docker compose ps
```
> See our [Docker Guide](docs/docker-guide.md) for more info.

### Kubernetes Deployment Path
To deploy to a cluster or Minikube:
```bash
kubectl apply -k infra/kubernetes/base
kubectl get pods -n llm-serving
```
> See our [Kubernetes Guide](docs/kubernetes-guide.md) for details on scaling, resources, and IPC sockets.

## 🗂️ Documentation Navigation

| Topic | Link |
|---|---|
| **Architecture** | [Architecture Overview](docs/architecture/overview.md) |
| **Local Setup & Docker** | [Docker Guide](docs/docker-guide.md) |
| **Kubernetes** | [Kubernetes Deployment Guide](docs/kubernetes-guide.md) |
| **Troubleshooting** | [Troubleshooting Guide](docs/troubleshooting.md) |
| **Configuration** | [Configuration Guide](docs/configuration.md) |
| **Security & Secrets** | [Security Guide](docs/security/threat_model.md) |

## 🧭 Choose Your Path
- **I want to run the project locally**: Start with the [Docker Guide](docs/docker-guide.md).
- **I want to deploy the project**: Read the [Kubernetes Guide](docs/kubernetes-guide.md).
- **I am troubleshooting an issue**: Check the [Troubleshooting Guide](docs/troubleshooting.md).
- **I want to understand the vLLM Memory Sharing**: View the [Architecture Overview](docs/architecture/overview.md) and the `kvcached` documentation.

## 📂 Repository Structure Guide
- `apps/gateway`: FastAPI ingress handling admission and caching.
- `apps/agent-worker`: Orchestrator for complex workflows.
- `infra/kubernetes/base`: Kustomize manifests for cluster deployment.
- `docs/`: Comprehensive guides and architecture diagrams.
- `docker-compose.yml`: Local multi-container orchestration.
