# 🚀 Inference Tuning & Sizing Guide

This guide provides practical engineering recommendations for tuning inference engines (vLLM and Ollama) across different **hardware setups** (from 8 GB consumer laptops to 80 GB enterprise GPUs and CPU fallbacks) and **model architectures** (Llama, Qwen, Mistral, Gemma, Phi).

---

## 💾 1. Understanding VRAM Budgeting & PagedAttention

vLLM uses **PagedAttention** to allocate KV cache memory dynamically in discrete blocks, avoiding fragmentation. The total VRAM available to an inference engine is divided into three distinct buckets:

$$\text{VRAM}_{\text{Total}} \times \text{gpu\_memory\_utilization} = \text{Model Weights} + \text{Activation Overhead} + \text{KV Cache Pool}$$

### Practical Memory Allocation Strategy:
- **CUDA Runtime & PyTorch Overhead:** Typically reserves ~0.5 GB – 1.0 GB of VRAM.
- **`--gpu-memory-utilization`:** 
  - For a **dedicated single engine**, set to `0.85` – `0.90` (leaving 10–15% headroom for activation peaks during prefill).
  - For **co-located dual engines** on a single GPU (e.g., responder + agents), partition the memory safely so the sum does not exceed `0.75` – `0.80` (e.g., `0.45` + `0.30` or `0.38` + `0.22`).

---

## 🎛️ 2. Hardware Sizing & Recommended Model Configurations

The platform is completely model-agnostic. You can serve any model family supported by vLLM and Ollama:

| Hardware Tier | Memory Budget | Recommended Models (Precision/Format) | Recommended Settings |
| :--- | :--- | :--- | :--- |
| **CPU Only / Dev Mode** | System RAM | `llama3.2:1b`, `llama3.2:3b`, `qwen2.5:0.5b`, `phi3:mini` (Ollama GGUF Q4_K_M) | Run via Ollama or set `USE_MOCK=True` |
| **8 GB – 12 GB GPU** *(e.g. RTX 3060, 4060, 4070, 5070)* | 8 – 12 GB VRAM | **Default Dual-Engine:** `Qwen2.5-1.5B` (Precision) + `Qwen2.5-0.5B` (Throughput/Multi-LoRA)<br/>**Single-Engine:** `Llama-3.1-8B` (AWQ/GPTQ 4-bit) | `--gpu-memory-utilization 0.45` (Precision)<br/>`--gpu-memory-utilization 0.30` (Throughput)<br/>`--max-model-len 2048` |
| **16 GB GPU** *(e.g. RTX 4080, 5080, T4, V100)* | 16 GB VRAM | **Dual-Engine:** `Llama-3.2-3B` + `Qwen2.5-1.5B`<br/>**Single-Engine:** `Llama-3.1-8B` (AWQ or BF16 unquantized), `Mistral-7B` | `--gpu-memory-utilization 0.85`<br/>`--max-model-len 4096` |
| **24 GB GPU** *(e.g. RTX 3090, 4090, A10G, L4)* | 24 GB VRAM | **Dual-Engine:** `Llama-3.1-8B` + `Qwen2.5-3B`<br/>**Single-Engine:** `Qwen2.5-14B` (AWQ), `Llama-3.1-8B` (FP16/BF16) | `--gpu-memory-utilization 0.90`<br/>`--max-model-len 8192` |
| **40 GB – 80 GB Cloud** *(e.g. A100, H100)* | 40 – 80 GB VRAM | `Llama-3.1-70B` (AWQ/FP8), `Qwen2.5-72B` (AWQ), or high-concurrency 8B models | Max batching concurrency (`max_num_seqs: 256`), chunked prefill enabled |

---

## ⚡ 3. Quantization vs Model Quality

When operating under memory constraints, choosing the right quantization format is critical:

1. **AWQ (Activation-aware Weight Quantization) 4-bit:**
   - Retains 99%+ of FP16 accuracy by preserving salient weight channels.
   - Shrinks an 8B model from ~16 GB down to ~4.5 GB, freeing >60% of GPU memory for KV cache and concurrency.
2. **FP8 (Floating Point 8):**
   - Ideal for modern architectures (Ada Lovelace, Blackwell, Hopper).
   - High throughput with minimal degradation.
3. **Unquantized (BF16/FP16):**
   - Use when memory allows (e.g. 0.5B to 3B models on 8–16GB GPUs, or 8B models on 24GB+ GPUs).

---

## 🧠 4. Prefix Caching Optimization

Automatic Prefix Caching (APC) allows vLLM to reuse KV cache blocks across requests that share identical initial prompt tokens (such as system instructions, few-shot examples, and tool definitions):

- **Enable APC:** Add `--enable-prefix-caching` to the vLLM container command arguments.
- **Deterministic Prompt Construction:**
  - Sort tool schemas and function signatures alphabetically so the prefix string is bit-for-bit identical across calls.
  - **Never** inject dynamic variables (timestamps, nonces, session IDs) into the beginning of the prompt; append dynamic metadata at the end of the context instead.
- **Cache Hit Verification:** Monitor the `vllm:gpu_prefix_cache_hit_rate` Prometheus metric exposed on `/metrics`.

---

## 🔄 5. Chunked Prefill & Speculative Decoding

- **Chunked Prefill (`--enable-chunked-prefill`):**
  - Breaks large prompt prefills into chunks, interleaving them with decode steps from active requests.
  - Drastically reduces Time-To-First-Token (TTFT) variance and prevents decode starvation in high-concurrency environments.
- **Speculative Decoding:**
  - Uses a small draft model (e.g. `Llama-3.2-1B`) to propose tokens verified in parallel by the target model (e.g. `Llama-3.1-8B`).
  - Useful for latency-critical single-batch workloads; for high-throughput multi-tenant environments, standard continuous batching with Multi-LoRA yields higher tokens-per-second per dollar.
