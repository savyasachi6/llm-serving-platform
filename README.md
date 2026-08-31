# Agentic LLM Serving Platform

A high-throughput, cost-efficient, caching-aware serving layer designed specifically for multi-agent LLM workflows. It serves as the intelligent bridge between client applications and underlying LLMs (like vLLM or Ollama), enforcing admission control, providing tenant-isolated caching, and abstracting the orchestration of complex AI tasks.

## 🚀 Key Features

*   **Bounded Admission Control:** Prevents system overload by shedding excess load (HTTP 503) instead of letting requests hang indefinitely in unbounded queues.
*   **Heterogeneous Workload Routing:** Dynamically routes traffic based on workload type (e.g., routing complex reasoning to an 8-bit Gemma model, and high-volume text transformations to a 4-bit Llama model).
*   **Multi-LoRA Dynamic Hot-Swapping:** A single vLLM instance serves multiple fine-tuned models (LoRA adapters) simultaneously on the same base model. The `triage` and `redactor` agents dynamically request specialized LoRAs (`reasoning` and `reflection`) at runtime, and vLLM hot-swaps them in milliseconds.
*   **Micro-Agent Assembly Line:** Discards brittle "Genius Agent" patterns in favor of single-shot, hyper-focused micro-agents (Triage, Redact, Respond) that scale flawlessly on smaller 2B-3B models.
*   **Strict Tenant Isolation:** Exact-match semantic caching respects `tenant_scope` and `auth_scope`, guaranteeing cross-tenant data boundaries. *(See the [Threat Model Mitigation Guide](docs/security/threat_model.md#1-cross-tenant-data-leakage-via-cache) for details on how cache keys are cryptographically enforced to prevent data leakage).*
*   **Prefix-Caching Optimization:** Implements a deterministic Prompt Builder designed to maximize Prefix Caching hits on engines like vLLM.
*   **Cloud Native (GPU Time-Slicing):** Fully containerized and orchestrated via Kubernetes. Utilizes NVIDIA GPU Time-slicing to share a single physical GPU across multiple heterogeneous model nodes locally.

## 🏗️ Architecture

The monorepo contains several distinct modules:

*   **`apps/gateway`**: The FastAPI ingress service handling admission, caching, and routing.
*   **`apps/agent-worker`**: The orchestrator for complex multi-agent workflows (implementing a robust Task Graph).
*   **`apps/playground`**: A Vite/React frontend UI to interact with the models and agents.
*   **`packages/*`**: Shared libraries containing Contracts, Prompt-Engine hashing, and Retrieval (VectorDB) logic.
*   **`infra/*`**: Docker Compose and Kubernetes Kustomize configurations for deployment (including definitions for all apps).

For detailed architecture diagrams, refer to [Architecture Overview](docs/architecture/overview.md).

## 🧠 Model Architecture & Storage

| Workload Role | Model / Adapter | Quantization | Engine / Target | Source / Location |
| :--- | :--- | :--- | :--- | :--- |
| **Triage & Classification** | `meta-llama/Llama-3.2-3B-Instruct` + `reasoning-lora` | 4-bit AWQ | vLLM | HuggingFace Hub / Container Cache |
| **PII Redaction & Security** | `meta-llama/Llama-3.2-3B-Instruct` + `reflection-lora`| 4-bit AWQ | vLLM | HuggingFace Hub / Container Cache |
| **Response Synthesis** | `meta-llama/Llama-3.2-3B-Instruct` | 4-bit AWQ | vLLM | HuggingFace Hub / Container Cache |
| **Local CPU/Dev Fallback** | `llama3:8b` | Q4_K_M | Ollama | Local Volume (`ollama_data`) |
| **Fast Dev & Unit Tests** | `MockBackend` | N/A | In-Memory / Python | 0s Boot / Zero Weights |

> For in-depth instructions on local testing, Docker Compose, and cloud deployments, see the [Testing & Execution Guide](docs/operations/testing_and_running_guide.md).
> To understand how Docker, Kubernetes, and the Gateway communicate, see the [System Architecture & Flow Guide](docs/architecture/system_flow_guide.md).

## 🧪 Testing & Quick Run

### 1. Run Automated Test Suite
```bash
# Run all 20 unit, integration, and security tests
uv run pytest -v
# or with direct virtualenv:
.\.venv\Scripts\python -m pytest -v
```

### 2. Run Micro-Agent Assembly Line Pipeline
Test the complete concurrent triage $\to$ PII redaction $\to$ response synthesis pipeline:
```bash
python scripts/test_micro_agents.py
```

### 3. Run the Playground UI
To test the frontend locally:
```bash
cd apps/playground
npm install
npm run dev
```

## 💻 Running Locally (Docker Compose)

The easiest way to start development is using Docker Compose. It spins up all application services (Gateway, Agent Worker, Playground UI), infrastructure (Redis, Qdrant), and an inference engine (Ollama or vLLM).

> **Note:** The `localhost` URLs below are Docker Compose port mappings from container ports to your host machine. Inside the containers, services communicate via Docker Compose DNS names (e.g., the agent-worker calls the gateway at `http://gateway:8000`, not `localhost`).

1. **Clone and prepare the environment:**
   ```bash
   cp .env.example .env
   ```
2. **Start the Local Stack:**
   ```bash
   docker compose -f infra/compose/docker-compose.yml --profile local up -d --build
   ```
3. **Access Services (from your browser):**
   * Gateway API Docs: `http://localhost:8000/docs`
   * Playground UI: `http://localhost:3000`
   * Agent Worker API: `http://localhost:8001`
   * Qdrant Dashboard: `http://localhost:6333/dashboard`

*(To run the full stack with the vLLM GPU engine, append `--profile gpu` to the compose command).*

## ☁️ Deploying to Kubernetes (GCP / Local)

The platform is designed to scale horizontally on Google Kubernetes Engine (GKE) or test locally via Docker Desktop / KinD using **Kustomize**.
The Kubernetes manifests are located in `infra/kubernetes/base` and deploy the entire stack: `gateway`, `agent-worker`, `playground` (UI), and `vllm`.

> **Important:** In Kubernetes, services communicate via **internal DNS names** (e.g., `http://gateway:80`, `http://agent-worker:8001`), not `localhost`. To access services from your browser, use `kubectl port-forward`. See the [System Architecture & Flow Guide](docs/architecture/system_flow_guide.md) for the full service communication map.

To deploy locally using `kubectl`:
```bash
kubectl apply -k infra/kubernetes/base
```

To access services from your browser after deploying:
```bash
kubectl port-forward svc/gateway 8000:80
kubectl port-forward svc/playground 3000:80
kubectl port-forward svc/agent-worker 8001:8001
```

Refer to the [Kubernetes Deployment Guide](docs/operations/kubernetes_guide.md) and [Testing & Execution Guide](docs/operations/testing_and_running_guide.md) for step-by-step instructions.
