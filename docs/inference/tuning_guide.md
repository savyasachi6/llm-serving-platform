# Inference Tuning Guide

## Context Budgets and PagedAttention
vLLM uses PagedAttention which splits KV cache into blocks. To optimize memory usage on constrained GPUs (like the RTX 5070 Ti with 12GB):
1. **Model Selection:** Use AWQ 4-bit quantization for 8B models, reducing weight footprint to ~4.5GB, leaving ~6GB for KV Cache.
2. **GPU Memory Utilization:** Set `--gpu-memory-utilization 0.85`. Do not go above 0.90 to avoid OOM during prefill spikes.
3. **Max Model Length:** Hard cap to `4096` tokens.

## Prefix Caching
Prefix caching enables reuse of the KV cache across requests that share a common prefix.
- Ensure tools are sorted deterministically.
- Do NOT inject timestamps or session IDs into the system prompt.
