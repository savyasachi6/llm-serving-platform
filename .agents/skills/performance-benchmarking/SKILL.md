---
name: performance-benchmarking
description: Execute reproducible, synthetic load tests to evaluate throughput, latency (TTFT/ITL), and cache hit ratios without using private data.
---

# Skill: Performance Benchmarking

## Purpose
Execute reproducible, synthetic load tests to evaluate throughput, latency (TTFT/ITL), and cache hit ratios without using private data.

## Pre-Checks
1. Confirm the gateway and target backends are in a healthy state (`/readyz`).
2. Verify benchmark scenario files exist in `benchmarks/scenarios/`.
3. Confirm strictly synthetic datasets are selected.

## Stepwise Workflow
1. Execute single-variable baseline test (`short_chat.yaml`).
2. Run shared-prefix multi-agent test (`shared_prefix_agents.yaml`) to evaluate prefix-caching gain.
3. Run long RAG prefill test (`long_rag.yaml`) to evaluate chunked prefill impact.
4. Run saturation test (`overload.yaml`) to verify admission rejection (HTTP 429/503) and graceful recovery.
5. Generate CSV/JSON summary metrics in `benchmarks/results/`.

## Validation Commands
```bash
python benchmarks/runner/load_generator.py --scenario benchmarks/scenarios/short_chat.yaml
```

## Deliverables

* Requests/sec, Output tokens/sec, p50/p95/p99 latency, TTFT, and prefix cache hit rate.
