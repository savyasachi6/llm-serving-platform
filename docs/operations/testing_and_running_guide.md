# 🧪 Testing & Execution Guide: Local vs Cloud & Model Architecture

This guide explains **how models are sourced and stored**, **how to run automated tests**, and **how to run the platform** across different environments (Pure Local, Docker Compose, Local Kubernetes with GPU Time-Slicing, and Cloud GKE).

---

## 🧠 1. Where Are the Models?

The platform uses a **heterogeneous multi-model + Multi-LoRA architecture**. Models are retrieved and stored differently depending on whether you run locally or in the cloud:                               ┌────────────────────────────────────────────────────────┐
                               │                   Hugging Face Hub                     │
                               │  - meta-llama/Llama-3.2-3B-Instruct (AWQ 4-bit)        │
                               │  - PandurangMopgar/Llama-3.2-3B-Instruct-reasoning-lora│
                               │  - justmalhar/llama-3.2-3B-Instruct-Reflection-LoRA    │
                               └──────────────────────────┬─────────────────────────────┘
                                                          │ (Startup Download / Cache)
                     ┌────────────────────────────────────┴─────────────────────────────────────┐
                     ▼                                                                          ▼
      ┌─────────────────────────────┐                                            ┌─────────────────────────────┐
      │   Cloud (GKE / Kubernetes)  │                                            │      Local Environment      │
      ├─────────────────────────────┤                                            ├─────────────────────────────┤
      │ • Pod: vllm                 │                                            │ • Option 1: Mock Backend    │
      │   - Base Llama-3.2-3B       │                                            │   (Zero weights, 0s boot)   │
      │   - LoRA: reasoning, reflect│                                            │ • Option 2: Ollama (CPU/GPU)│
      │ • Cache: Persistent Volume  │                                            │   - llama3:8b               │
      │   or ~/.cache/huggingface   │                                            │ • Option 3: Local KinD vLLM │
      └─────────────────────────────┘                                            │   (Single Model Multi-LoRA) │
                                                                                 └─────────────────────────────┘

### A. Primary Production Architecture (Qwen Family in Kubernetes & Root Compose)
- **High-Accuracy Synthesis & Reasoning Node (`vllm-responder`)**:
  - `Qwen/Qwen2.5-1.5B-Instruct` (Unquantized, high-precision token generation).
- **High-Throughput Multi-LoRA Node (`vllm-agents`)**:
  - Base: `Qwen/Qwen2.5-0.5B-Instruct`
  - `reasoning-lora`: `wuyanzu4692/task-13-Qwen-Qwen2.5-0.5B-Instruct` (Intent classification & triage)
  - `reflection-lora`: `Hebisuke/Qwen2.5-0.5B-Instruct_bias2_0.5B` (PII redaction & compliance)
- **Local LoRA Checkpoint Script**: Run `python scripts/download_real_loras.py` to fetch genuine adapter checkpoints directly to `lora_adapters/`.

### B. Alternative Multi-Profile Stack (`infra/compose/docker-compose.yml`)
- **vLLM Responder**: `meta-llama/Llama-3.2-3B-Instruct`
- **vLLM Agents**: `meta-llama/Llama-3.2-3B-Instruct` (AWQ 4-bit) with text2sql and reflection LoRAs.

### C. Local Development Environments
1. **Mock Backend (Default / Fast Dev)**:
   - Set `USE_MOCK=True`. Requires **no GPU and no weight downloads** (0s boot time).
   - Simulates backend token streaming, latency profiles, and OpenAI-compatible completions.
2. **Ollama Engine (Local CPU or single GPU)**:
   - Weights stored in the local Ollama volume (`~/.ollama/models` or Docker volume `ollama_data`).
   - Run `ollama pull qwen2.5:1.5b-instruct-q4_K_M` (or `llama3:8b`).
3. **Local Workstation / Docker Desktop (GPU with `kvcached`)**:
   - Uses `kvcached` dynamic IPC memory manager (`/tmp/kvcached-ipc/kvcached.sock`) to arbitrate VRAM across engines without OOMs.

---

## 🧪 2. How to Test

### A. Run Automated Pytest Suite
Run the complete test suite (Unit tests, Integration tests, Contract tests, Redaction security tests, and Benchmark performance tests):

```bash
# Using uv:
uv run pytest -v

# Or using the local virtualenv directly:
.\.venv\Scripts\python -m pytest -v
```

### B. Run Individual Test Layers
```bash
# Gateway unit tests (Admission control, Cache key determinism, Routing):
.\.venv\Scripts\python -m pytest apps/gateway/tests/unit/ -v

# OpenAI API contract validation:
.\.venv\Scripts\python -m pytest apps/gateway/tests/contract/ -v

# Backend integration tests:
.\.venv\Scripts\python -m pytest apps/gateway/tests/integration/ -v

# Multi-Agent worker tests:
.\.venv\Scripts\python -m pytest apps/agent-worker/tests/ -v

# Security & PII Redaction tests:
.\.venv\Scripts\python -m pytest tests/security/ -v

# End-to-End full chat workflow:
.\.venv\Scripts\python -m pytest tests/e2e/ -v
```

---

## 🚀 3. How to Run Locally

### Mode 1: Local Development Server (Mock / FastAPI)
Ideal for testing routing logic, caching, admission control, and agent orchestration with instant start:

1. **Activate Virtual Environment:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

2. **Start the Gateway (Mock mode enabled):**
   ```bash
   # Run Gateway using uv workspace:
   uv run uvicorn app.main:app --app-dir apps/gateway --host 0.0.0.0 --port 8000 --reload
   ```

3. **Verify Gateway Health & Documentation:**
   - Swagger / OpenAPI UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Health Probes: [http://localhost:8000/health](http://localhost:8000/health) and [http://localhost:8000/healthz](http://localhost:8000/healthz)
   - Readiness Probe: [http://localhost:8000/readyz](http://localhost:8000/readyz)

4. **Send a Test Chat Completion Request:**
   ```bash
   curl -X POST http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "X-Tenant-ID: tenant-alpha" \
     -d '{
       "model": "triage",
       "messages": [
         {"role": "user", "content": "My account was double billed $50 on invoice 12345"}
       ]
     }'
   ```

---

### Mode 2: Docker Compose (Gateway + Redis + Qdrant + Ollama / GPU)

1. **Prepare Environment File:**
   ```bash
   cp .env.example .env
   # Add your HF_TOKEN in .env if testing GPU profiles
   ```

2. **Start the Local Development Stack (CPU / Ollama):**
   ```bash
   docker compose -f infra/compose/docker-compose.yml --profile local up -d --build
   ```

3. **Start with Local GPU (vLLM Engine):**
   ```bash
   docker compose -f infra/compose/docker-compose.yml --profile local --profile gpu up -d --build
   ```

4. **Stop Services:**
   ```bash
   docker compose -f infra/compose/docker-compose.yml down
   ```

---

### Mode 3: Local Kubernetes (KinD / Docker Desktop with GPU Time-Slicing)

To run heterogeneous dual-model inference on a single physical GPU:

1. **Apply GPU Time-Slicing ConfigMap:**
   ```bash
   kubectl apply -f infra/kubernetes/kind/gpu-time-slicing.yaml
   ```

2. **Patch NVIDIA Device Plugin to Enable 4 Virtual GPUs:**
   ```bash
   kubectl patch daemonset nvidia-device-plugin-daemonset -n kube-system \
     --type='json' \
     -p='[{"op": "add", "path": "/spec/template/spec/containers/0/args", "value": ["--config-file=/etc/kubernetes/nvidia-config/any"]}]'
   ```

3. **Deploy the Base Infrastructure:**
   ```bash
   # Deploy Redis, Gateway, vLLM Precision, and vLLM Throughput with Multi-LoRA
   kubectl apply -k infra/kubernetes/base
   ```

4. **Check Pod Status:**
   ```bash
   kubectl get pods -o wide
   ```

---

## ☁️ 4. How to Run in Cloud (Google Kubernetes Engine - GKE)

1. **Create HuggingFace Secret in Cluster:**
   ```bash
   kubectl create secret generic hf-token --from-literal=token="hf_your_actual_token_here"
   ```

2. **Deploy GKE Overlay with Autoscaling and Ingress:**
   ```bash
   kubectl apply -k infra/kubernetes/overlays/gcp
   ```

3. **Verify Load Balancer IP:**
   ```bash
   kubectl get ingress gateway-ingress
   ```

---

## 📊 5. Benchmarking & Synthetic Load Testing

Run reproducible synthetic load tests against the Gateway:

```bash
# Run benchmark against local or cloud gateway
python benchmarks/runner/load_generator.py \
  --target-url http://localhost:8000 \
  --concurrency 10 \
  --requests 100 \
  --tenant-id tenant-benchmark
```
