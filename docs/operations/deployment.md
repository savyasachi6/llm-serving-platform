# Deployment & Scaling Guide

This document explains how the platform runs, the relationship between Docker and Kubernetes, and how to scale the system.

## Docker vs. Kubernetes: How they work together

To understand how the platform runs, it helps to understand the progression from code to production:

1. **Docker (The Packaging):** Docker is used to package your application (like the Gateway) and its dependencies into a standard, runnable unit called a "Container Image". Think of it as a shipping container. We define what goes into this container in the `Dockerfile`.
2. **Docker Compose (Local Development):** `docker-compose.yml` is a tool for running multiple Docker containers locally on a single machine. It spins up the Gateway, Redis, vLLM, and Ollama all on your laptop or a single development server.
3. **Kubernetes (Production Orchestration):** When you move to production, running containers on a single machine isn't enough. You need multiple servers (a cluster). Kubernetes is the "orchestrator" that manages these containers across many servers. 

**Does Kubernetes use Docker?**
Yes and no. Kubernetes runs the exact same *Docker Images* that you built. However, modern Kubernetes technically uses a lightweight runtime behind the scenes (like `containerd` or `CRI-O`) instead of the full "Docker Desktop" engine to run them. But conceptually, Kubernetes is just a giant, multi-server version of Docker Compose that handles self-healing, load balancing, and auto-scaling.

## Deployment Environments

### Local Development (Docker Compose)
For local testing, benchmarking, and development, use Docker Compose.

```bash
# Start the core gateway and local fallback engine (Ollama)
docker compose --profile local up -d --build

# Start the full stack including the heavy vLLM GPU engine
docker compose --profile local --profile gpu up -d --build
```

### Production Scaling (Kubernetes)
In production, you want the system to scale based on traffic. The `infra/kubernetes/` directory contains the manifests.

- **Gateway Scaling:** The Gateway is lightweight (Python/FastAPI). Kubernetes can easily scale this from 3 replicas to 100 replicas based on CPU usage or HTTP request volume.
- **vLLM Scaling:** Scaling the vLLM backend is harder because it requires GPUs. In Kubernetes, you would configure an Autoscaler to watch the queue depth of vLLM. If the queue gets too long, Kubernetes requests a new GPU node from the cloud provider, pulls the Docker image, and spins up a new vLLM instance to handle the load.

## Model Profiles
Because GPU VRAM is highly constrained (e.g., 12.2 GB on an RTX 5070 Ti), the exact configurations for the inference engines are stored in `infra/vllm/model-profiles/` and `infra/ollama/model-profiles/`. These profiles dictate the maximum context length, batch size, and memory utilization to prevent Out-Of-Memory (OOM) crashes.
