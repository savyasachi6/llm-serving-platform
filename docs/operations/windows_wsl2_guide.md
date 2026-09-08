# Windows WSL2 Getting Started Guide

Running a multi-agent, GPU-accelerated LLM system locally on Windows requires specific configurations to bridge the gap between Windows and Linux native tools like `vLLM` and `kvcached`. This guide explains how the architecture works on Windows and provides step-by-step commands for a new user to get up and running.

---

## 1. How It Works on Windows

The LLM Serving Platform leverages **WSL2 (Windows Subsystem for Linux)**.

- **The Host (Windows)**: You install the standard NVIDIA drivers on Windows. You **do not** install Linux NVIDIA drivers.
- **The VM (WSL2)**: Microsoft automatically mounts the Windows NVIDIA drivers into the WSL2 Linux environment (via DirectX/WDDM). This gives Linux apps direct, near-native access to your physical GPU.
- **The Containers (Docker)**: Docker Desktop runs its engine inside WSL2. When we spin up the `vllm-responder`, `vllm-agents`, and `kvcached` containers, they utilize the `nvidia-container-toolkit` to talk to the GPU just as they would on a bare-metal Linux server.

> [!NOTE] 
> Because of how WSL2 manages memory, the `vLLM` engine requires a specific environment variable (`VLLM_WSL2_ENABLE_PIN_MEMORY=1`) to prevent freezing during startup. This is automatically handled in our `docker-compose.yml` and manual run commands.

---

## 2. Prerequisites Checklist

Before you start, ensure you have the following installed and configured on your Windows machine:

1. **Windows Subsystem for Linux (WSL2)**:
   - Open PowerShell as Administrator and run: `wsl --install`
   - Ensure you are using Ubuntu (default).
2. **NVIDIA Game Ready or Studio Drivers**:
   - Installed normally on Windows.
3. **Docker Desktop**:
   - Install Docker Desktop for Windows.
   - Go to **Settings > Resources > WSL Integration** and ensure integration is enabled for your Ubuntu distro.
4. **Python (via `uv`)**:
   - We recommend using `uv` (the fast Python package installer) inside your WSL2 environment.

---

## 3. Optimizing WSL2 Memory Limits

By default, Windows might restrict how much RAM the WSL2 VM can use, which can lead to Out-Of-Memory (OOM) kills when downloading or loading large models.

1. Open File Explorer in Windows.
2. Navigate to `%USERPROFILE%` (e.g., `C:\Users\YourName`).
3. Create or edit a file named `.wslconfig`.
4. Add the following to give WSL2 sufficient resources (adjust `memory` based on your total system RAM, but give it at least 16GB if possible):

```ini
[wsl2]
memory=16GB
processors=4
swap=8GB
```

5. Restart WSL by opening PowerShell and running: `wsl --shutdown`

---

## 4. Step-by-Step Execution

Follow these steps **inside your WSL2 Ubuntu Terminal** (not Windows PowerShell).

### Step 1: Open WSL2 and Clone the Repository
Open your Ubuntu terminal from the Start menu.

```bash
# Clone the repository
git clone https://github.com/savyasachi6/llm-serving-platform.git
cd llm-serving-platform
```

### Step 2: Download the LoRA Adapters
The Multi-LoRA architecture requires specific fine-tuned adapters. We provide a script to download these securely via Hugging Face.

```bash
# We use uv to run the script securely in an isolated environment
uv run python scripts/lora/download_loras.py
```
*Note: This will download the adapters into the `./lora_adapters` folder.*

### Step 3: Start the GPU-Accelerated Stack
We use Docker Compose to spin up the entire architecture (Gateway, Agent Worker, Redis, kvcached, and dual vLLM engines).

```bash
# Start the full GPU profile stack in the background
docker compose -f infra/compose/docker-compose.yml --profile gpu up -d --build
```

### Step 4: Verify the Services
Check the logs to ensure the inference engines are ready and `kvcached` successfully bound to the IPC socket.

```bash
# Watch the logs for the responder engine
docker logs -f llm-vllm-responder

# Watch the logs for the agents engine
docker logs -f llm-vllm-agents
```
*Wait until you see "Uvicorn running on http://0.0.0.0:8080" in the logs.*

### Step 5: Interact with the System
Once everything is running, you can access the system from your Windows web browser!

- **Frontend Playground UI**: Open [http://localhost:3000](http://localhost:3000) to chat with the agents.
- **API Swagger Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs) for the Gateway API.
- **Interactive VRAM Visualizer**: Run the explainer tool in your WSL terminal:
  ```bash
  uv run python scripts/kvcached_visualizer/serve.py --serve
  ```
  Then open the provided localhost link in your browser.

---

## 5. Shutting Down & Cleanup

When you are finished, it is important to shut down the containers to free up your GPU VRAM and system memory.

```bash
# Stop all containers
docker compose -f infra/compose/docker-compose.yml --profile local --profile gpu down

# Optional: Free up disk space if you want to wipe cached models
docker system prune -f
```

---

## 6. Common WSL2 Troubleshooting

### "GPU not found" or CUDA errors inside Docker
- **Fix**: Open Windows Task Manager, go to Performance, and verify your GPU is visible. Ensure Docker Desktop's "WSL Integration" is turned on for Ubuntu. Do **not** install the `nvidia-cuda-toolkit` via `apt` inside Ubuntu. 

### vLLM freezes at "Capturing CUDA graph"
- **Fix**: This is a known WSL2 memory pinning issue. Ensure the `VLLM_WSL2_ENABLE_PIN_MEMORY=1` environment variable is set. This is already included in our `docker-compose.yml` and manual `docker run` guides.

### "VmmemWSL" process consuming all Windows RAM
- **Fix**: Linux caches filesystem data aggressively. If you want to drop the cache manually without shutting down WSL, run this inside your Ubuntu terminal:
  ```bash
  sudo echo 3 > /proc/sys/vm/drop_caches
  ```
  Or, set a hard limit in the `.wslconfig` file as detailed in Step 3.

---

## 7. Stress Testing on WSL2

We provide an automated bash script to stress test the Gateway and inference engines to verify throughput and elasticity. 

### What it tests
1. **Concurrency Boundaries**: Can the Gateway queue handle bursts without 504 Timeouts?
2. **KV-Cache Elasticity**: Does `kvcached` safely pool memory under heavy sequence load without OOMs?
3. **Multi-LoRA Sweeping**: The overhead latency of hot-swapping adapters under load.
4. **Admission Control**: Does the system shed extreme load gracefully with HTTP 429s?

### Running the All-in-One Suite

The automated script handles the entire workflow end-to-end:
1. Verifies Docker Desktop is running and WSL2 integration is active.
2. Automatically starts your chosen stack (Kubernetes via Minikube or Docker Compose) if not already online.
3. Automatically establishes port-forwarding and verifies API Gateway readiness (`/healthz`).
4. Executes all benchmark scenarios (`short_chat`, `shared_prefix_agents`, `long_rag`, `overload`).
5. Collects structured metrics and generates summary reports in `benchmarks/results/`.

```bash
# Run all-in-one test on Kubernetes (Minikube):
bash scripts/run_stress_tests.sh --target k8s

# Or run all-in-one test on Docker Compose:
bash scripts/run_stress_tests.sh --target compose
```

### Collected Benchmark Artifacts
All benchmark results are automatically collected and saved in `benchmarks/results/`:
- `benchmarks/results/stress_test_<timestamp>.md` - Formatted Markdown summary table with latency percentiles (p50, p95, p99) and throughput.
- `benchmarks/results/stress_test_<timestamp>.json` - Raw metrics per scenario for programmatic analysis.
- `benchmarks/results/stress_test_<timestamp>.log` - Full execution log with per-request details.
- `benchmarks/results/latest_report.md` - Convenience pointer to the latest run report.

