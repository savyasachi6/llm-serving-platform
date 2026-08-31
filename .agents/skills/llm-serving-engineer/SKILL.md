---
name: llm-serving-engineer
description: Configure, profile, and tune high-throughput inference engines (vLLM primary, Ollama fallback) with bounded resources.
---

# Skill: LLM Serving Engineer

## Purpose
Configure, profile, and tune high-throughput inference engines (vLLM primary, Ollama fallback) with bounded resources.

## Pre-Checks
1. Check available hardware (`nvidia-smi` / NPU status).
2. Inspect target model parameter size, context window (`max_model_len`), and quantization format.
3. Compute baseline VRAM budget:
   - Model Weights (GB) + Base CUDA Context (GB) + KV Cache Allocation = Total Target VRAM.

## Stepwise Workflow
1. Select target model profile from `infra/vllm/model-profiles/`.
2. Configure `gpu_memory_utilization` conservatively (default: 0.85-0.90).
3. Set `max_num_seqs` to match the gateway admission semaphore limit.
4. Enable `--enable-prefix-caching` for workloads with stable system prefixes.
5. If long RAG contexts are used, test chunked prefill (`--enable-chunked-prefill`) with a conservative token budget.
6. Validate configuration using `infra/scripts/validate_compose.sh` (or `docker compose config`).

## Validation Commands
```bash
docker compose --profile gpu config
uv run pytest packages/contracts/tests/
```

## Stop Conditions (Requires Human Approval)

* Downloading models > 1 GB.
* Allocating > 90% of available GPU VRAM.
* Enabling speculative decoding or multi-GPU tensor parallelism.
