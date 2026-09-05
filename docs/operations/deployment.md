# Deployment & Scaling Guide

This document outlines the deployment strategy for the platform, the relationship between the containerization and orchestration layers, and guidelines for scaling the system.

## Containerization and Orchestration

The platform relies on containerization to ensure consistency across environments, from local development to production scaling.

1. **Docker (Packaging):** Docker is used to package the application components (e.g., the Gateway, Agent Worker) and their dependencies into standard container images. The build instructions for these images are defined in the respective `Dockerfile`s.
2. **Docker Compose (Local Development):** `docker-compose.yml` provides a mechanism for running the multi-container stack locally. It orchestrates the Gateway, Redis, vLLM, and Ollama on a single development workstation or testing server.
3. **Kubernetes (Production Orchestration):** For production environments requiring high availability and horizontal scaling, Kubernetes serves as the orchestrator. It distributes the container images across a cluster of nodes, handling load balancing, self-healing, and auto-scaling.

**The Relationship Between Kubernetes and Docker:**
Kubernetes orchestrates the exact same container images built during the Docker workflow. While modern Kubernetes clusters typically use lightweight container runtimes (such as `containerd` or `CRI-O`) instead of the full Docker engine, the underlying container formats and execution principles remain identical.

## Deployment Environments

### Local Development (Docker Compose)
For local testing, benchmarking, and development workflows, Docker Compose provides two flexible paths:

1. **Root Standalone Stack (Default Qwen Family + `kvcached`)**:
   ```bash
   # Start Gateway, Agent Worker, Redis, kvcached, and Qwen Dual-Engine
   docker compose up -d --build
   ```

2. **Multi-Profile Infrastructure Stack (`infra/compose/docker-compose.yml`)**:
   ```bash
   # Start lightweight CPU stack with Ollama fallback:
   docker compose -f infra/compose/docker-compose.yml --profile local up -d --build

   # Start full GPU stack with Llama-3.2 + Observability:
   docker compose -f infra/compose/docker-compose.yml --profile local --profile gpu up -d --build
   ```

### Production Scaling (Kubernetes)
In production scenarios, the system is designed to scale dynamically based on traffic. The `infra/kubernetes/` directory contains the baseline manifests.

- **Gateway Scaling:** The Gateway is a lightweight Python/FastAPI application. Kubernetes can scale this deployment horizontally (e.g., from 3 to 100 replicas) based on standard metrics like CPU utilization or HTTP request rates.
- **vLLM Scaling:** Scaling the vLLM backend requires GPU provisioning. In a Kubernetes environment, a Cluster Autoscaler monitors the queue depth of pending vLLM pods. When capacity is reached, the autoscaler provisions new GPU-enabled nodes and schedules additional vLLM instances to distribute the inference load.

## Model Profiles and Hardware Constraints
GPU VRAM is typically the primary constraint for LLM inference (e.g., 12.2 GB on an RTX 5070 Ti). To prevent Out-Of-Memory (OOM) failures, specific configurations for the inference engines are maintained in `infra/vllm/model-profiles/` and `infra/ollama/model-profiles/`. These profiles enforce strict boundaries on maximum context length, batch size, and GPU memory utilization.
