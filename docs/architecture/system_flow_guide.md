# System Architecture & Flow Guide

This document breaks down how your local environment, Docker daemon, and Kubernetes cluster interact to power the Cost-Efficient LLM Serving Platform. 

---

## 1. The Core Infrastructure

At a high level, your machine is running three interconnected layers:

1. **Host Machine (Windows)**: Where you edit code, run local Python scripts (like the micro-agents), and use the Playground UI.
2. **Docker Desktop**: The virtualization engine that builds containers.
3. **Minikube (Native Windows GPU)**: A local Kubernetes cluster that runs inside a Docker driver. Unlike KinD, Minikube supports native `--gpus=all` passthrough for the NVIDIA Container Toolkit. It manages all application pods: Gateway, Agent Worker, Playground, and the vLLM Engines.

```mermaid
graph TD
    subgraph Host Machine
        A[Browser / Terminal] -->|HTTP Requests| B
        A -->|kubectl / docker| C[Docker Daemon]
    end
    
    subgraph Docker Desktop
        C -->|Builds| D(Gateway Image)
        C -->|Builds| D2(Agent Worker Image)
        C -->|Builds| D3(Playground Image)
        C -->|Runs| E[Minikube Node Container]
    end
    
    subgraph Kubernetes Cluster - Minikube
        E --> F[Gateway Pods x3]
        E --> G1[vLLM Precision Pod]
        E --> G2[vLLM Throughput Pod]
        E --> H[Agent Worker Pods x3]
        E --> I[Playground Pod]
        H -->|http://gateway:80| F
        F -->|http://vllm-responder:8080| G1
        F -->|http://vllm-agents:8080| G2
        I -->|http://agent-worker:8001| H
    end
```

---

## 2. How Services Communicate in Kubernetes

> **Key Concept: Kubernetes DNS**
> When you create a Kubernetes Service (e.g., `gateway-service.yaml` with `name: gateway`), Kubernetes automatically creates a DNS entry inside the cluster. Any pod can reach the gateway by simply calling `http://gateway:80`. No hardcoded IP addresses are needed.

This is why we **don't use `localhost`** in Kubernetes. Each pod is its own isolated network namespace — `localhost` inside the gateway pod only refers to the gateway container itself. To reach the vLLM engine, the gateway must use the **Service DNS name**: `http://vllm:8080`.

### Service Communication Map

| From | To | URL Used | Defined In |
| :--- | :--- | :--- | :--- |
| **Agent Worker** | Gateway | `http://gateway:80` | `agent-worker-deployment.yaml` (env: `GATEWAY_URL`) |
| **Gateway** | vLLM Precision | `http://vllm-responder:8080/v1` | `common/config.py` (env: `VLLM_RESPONDER_BASE_URL`) |
| **Gateway** | vLLM Throughput | `http://vllm-agents:8080/v1` | `common/config.py` (env: `VLLM_AGENTS_BASE_URL`) |
| **Gateway** | Ollama | `http://ollama:11434` | `common/config.py` (env: `OLLAMA_BASE_URL`) |
| **Playground UI** | Agent Worker | `http://agent-worker:8001` | Nginx config / frontend API calls |
| **Browser (local dev)** | Playground | `http://localhost:3000` or K8s port-forward | `docker-compose.yml` / `playground-service.yaml` |

---

## 3. Component Flow: What is Running What?

### The Gateway (`apps/gateway`)
- **What it is**: A high-performance Python FastAPI server.
- **Where it runs**: Inside Kubernetes as a Deployment (`gateway-deployment.yaml`). It scales between 3 to 20 pods via HPA.
- **Its Job**: Acts as the "front door". It checks admission limits, calculates cache hits (using tenant-scoped SHA-256 keys), and forwards requests to the appropriate backend (vLLM or Ollama).
- **Docker image**: Built from `apps/gateway/Dockerfile`.

### The Agent Worker (`apps/agent-worker`)
- **What it is**: A FastAPI service that orchestrates multi-agent workflows (TriageAgent, RedactAgent, RespondAgent).
- **Where it runs**: Inside Kubernetes as a Deployment (`agent-worker-deployment.yaml`). 3 replicas by default.
- **Its Job**: Receives raw customer tickets and breaks them into parallel micro-agent tasks, sending each prompt to the Gateway via its K8s DNS name (`http://gateway:80`).
- **Docker image**: Built from `apps/agent-worker/Dockerfile`.

### The Playground (`apps/playground`)
- **What it is**: A React/Vite frontend UI served by Nginx.
- **Where it runs**: Inside Kubernetes as a Deployment (`playground-deployment.yaml`). 1 replica.
- **Its Job**: Provides a browser interface for users to submit tickets and see the multi-agent pipeline in action.
- **Docker image**: Built from `apps/playground/Dockerfile` (multi-stage: Node.js build → Nginx serve).

### The vLLM Engines (`infra/kubernetes/base/*-deployment.yaml`)
- **What they are**: Two highly optimized C++/CUDA inference engines serving distinct roles.
- **Where they run**: Inside Kubernetes as distinct Pods.
- **Precision Node (`vllm-responder`)**: Holds the `Qwen/Qwen2.5-1.5B-Instruct` base model in GPU memory for complex, multi-step reasoning.
- **Throughput Node (`vllm-agents`)**: Holds the `Qwen/Qwen2.5-0.5B-Instruct` base model along with multiple LoRA adapters. When the Gateway routes a Triage request for `model="reasoning-lora"`, vLLM dynamically layers that adapter over the base model in milliseconds.

---

## 4. The Lifecycle of a Request (Step-by-Step)

```mermaid
sequenceDiagram
    participant Client as Playground UI
    participant Worker as Agent Worker<br/>(Orchestrator)
    participant Gateway as Gateway API
    participant Cache as Redis Cache
    participant VLLM_T as vLLM Throughput<br/>(Triage & Redact)
    participant VLLM_P as vLLM Precision<br/>(Respond)

    Client->>Worker: POST /api/process_ticket
    
    %% Parallel execution of Triage and Redact
    par Triage Agent
        Worker->>Gateway: POST /v1/chat/completions (triage)
        Gateway->>VLLM_T: Forward (model="reasoning-lora")
        VLLM_T-->>Gateway: Classification Result
        Gateway-->>Worker: Triage Complete
    and Redact Agent
        Worker->>Gateway: POST /v1/chat/completions (redact)
        Gateway->>VLLM_T: Forward (model="reflection-lora")
        VLLM_T-->>Gateway: Redacted Text
        Gateway-->>Worker: Redact Complete
    end
    
    %% Strict boundary: Respond cannot run until Redact succeeds
    Note over Worker: Strict Security Barrier:<br/>Redaction must succeed
    
    Worker->>Gateway: POST /v1/chat/completions (respond)
    Gateway->>Cache: Check Cache
    Cache-->>Gateway: Cache Miss
    Gateway->>VLLM_P: Forward (base Qwen 1.5B)
    VLLM_P-->>Gateway: Final Synthesized Response
    Gateway->>Cache: Set Cache
    Gateway-->>Worker: Response Complete
    Worker-->>Client: Final JSON Payload
```

1. You type a ticket into the **Playground UI** (running in K8s or locally at `http://localhost:3000`).
2. The UI sends the ticket to the **Agent Worker** (`http://agent-worker:8001/api/process_ticket` in K8s).
3. The **Orchestrator** splits the ticket and simultaneously dispatches to the `TriageAgent` and `RedactAgent`.
4. Each Agent sends its system prompt + user message to the **Gateway** (`http://gateway:80/v1/chat/completions`).
5. The Gateway applies **Admission Control** (rejects if overloaded with HTTP 503), checks the **exact-match cache**, and on a miss, routes to the **vLLM Throughput Node** (`http://vllm-agents:8080`) based on the workload type.
6. The Throughput Node dynamically hot-swaps to the correct LoRA adapter (`reasoning-lora` or `reflection-lora`).
7. Once Triage and Redact finish in parallel, the Orchestrator enforces a strict safety boundary (halting if PII redaction failed) and triggers the `RespondAgent`.
8. The `RespondAgent` calls the Gateway, which routes this specific workload to the **vLLM Precision Node** (`http://vllm-responder:8080`) for high-fidelity final synthesis.

---

## 5. The Import Architecture (How Python Packages Work)

This monorepo uses a **uv workspace** (defined in the root `pyproject.toml`). The workspace members are:
- `apps/gateway`
- `apps/agent-worker`
- `packages/common`, `packages/contracts`, `packages/prompt-engine`, `packages/retrieval`, `packages/evaluation`

The shared packages live under `packages/<name>/src/<name>/`. The root `pyproject.toml` configures `pythonpath` entries for pytest, and `uv run` automatically resolves workspace dependencies. This is why you can write:

```python
from contracts.openai_models import ChatCompletionRequest
from common.config import settings
```

These are **not** pip packages from PyPI. They are local workspace packages resolved by `uv`. The `contracts` module physically lives at `packages/contracts/src/contracts/openai_models.py`.

> **Why linters may complain:** Static analysis tools (like Pyrefly, Pylance) don't always understand `uv` workspace resolution. You may see "missing import" warnings — these are **false positives**. The code runs correctly because `uv run` handles the path resolution. You can suppress these with linter-specific comments, but they are not required for correctness.

---

## 6. Operational Commands Cheatsheet

### Build Docker Images
```bash
# Build all three application images from the repo root
docker build -t gateway:latest -f apps/gateway/Dockerfile .
docker build -t agent-worker:latest -f apps/agent-worker/Dockerfile .
docker build -t playground:latest -f apps/playground/Dockerfile apps/playground
```

### Apply Kubernetes Manifests
```bash
kubectl apply -k infra/kubernetes/base
```

### Restart Pods (after image rebuild)
```bash
kubectl rollout restart deployment gateway
kubectl rollout restart deployment agent-worker
kubectl rollout restart deployment playground
```

### Check Pod Status
```bash
kubectl get pods
```

### Port-Forward for Local Access
```bash
# Access gateway from your browser
kubectl port-forward svc/gateway 8000:80

# Access playground UI from your browser
kubectl port-forward svc/playground 3000:80

# Access agent-worker API
kubectl port-forward svc/agent-worker 8001:8001
```

---
## References
- For local testing options and architectural diagrams, see: [Testing & Running Guide](../operations/testing_and_running_guide.md).
- For Kubernetes deployment details, see: [Kubernetes Deployment Guide](../operations/kubernetes_guide.md).
- For security and tenant isolation, see: [Threat Model](../security/threat_model.md).
- To view the exact Kubernetes configurations, see: [Base Infrastructure](../../infra/kubernetes/base/).
