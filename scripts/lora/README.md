# 🧠 Multi-LoRA Adapter Tooling

This directory contains utilities to download, generate, and inspect Low-Rank Adaptation (LoRA) adapters used by the platform's throughput engine (`vllm-agents`).

---

## 🛠️ Available Scripts

### 1. Download Genuine Fine-Tuned Checkpoints
Downloads genuine, pre-trained LoRA weights from the Hugging Face Hub directly into `lora_adapters/`:
```bash
python scripts/lora/download_loras.py
```
- **`reasoning-lora`**: `wuyanzu4692/task-13-Qwen-Qwen2.5-0.5B-Instruct` (2.18 MB) - Multi-step instruction & math reasoning.
- **`reflection-lora`**: `Hebisuke/Qwen2.5-0.5B-Instruct_bias2_0.5B` (17.64 MB) - Reflective reasoning and PII sanitization.

### 2. Generate Offline Synthetic Adapters
Generates valid PEFT-compliant `adapter_config.json` and `adapter_model.safetensors` using only the Python standard library (no internet or PyTorch needed):
```bash
python scripts/lora/generate_adapters.py
```
Ideal for offline testing, CI/CD pipelines, or environments with restricted internet access.

---

## ⚡ How vLLM Uses These Adapters
When `vllm-agents` runs with `--enable-lora`, the Punica CUDA kernels dynamically swap these adapters on top of the shared base model per sequence token during continuous batching without restarting the container or allocating separate base model weights.
