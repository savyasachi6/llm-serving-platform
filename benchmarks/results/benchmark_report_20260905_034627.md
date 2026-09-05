# LLM Serving Platform - Stress Test Benchmark Report

- **Timestamp**: 20260905_034627
- **Target Environment**: K8S (Minikube on WSL2)
- **Total Scenarios Evaluated**: 4

## Performance Results Table

| Scenario | Workload | Concurrency | Total Req | Success Rate | Throughput | Latency p50 | Latency p95 | Latency p99 |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **long_rag** | reasoning | 5 | 50 | 100.0% | **0.68 req/s** | 1.410s | 62.835s | 63.378s |
| **overload** | chat | 100 | 1000 | 100.0% | **20.93 req/s** | 4.199s | 6.060s | 6.833s |
| **shared_prefix_agents** | chat | 10 | 100 | 100.0% | **16.18 req/s** | 0.501s | 1.050s | 1.421s |
| **short_chat** | chat | 10 | 100 | 100.0% | **11.58 req/s** | 0.787s | 1.372s | 1.991s |

## Key Observations & Architectural Validation

1. **Prefix Caching Speedup**:
   - `shared_prefix_agents` (which uses a common system prompt) achieved **16.18 req/s** with a **p50 latency of 0.501s**.
   - Comparing against `short_chat` at **11.58 req/s** and **0.787s**, prompt prefix caching delivered a **~40% throughput increase** and **~36% latency reduction**.

2. **High-Concurrency Saturation**:
   - `overload` pushed **1,000 requests** at **concurrency 100**.
   - The Gateway sustained **20.93 req/s** with zero 504 gateway timeouts and 100% request completion.

3. **Chunked Prefill on Reasoning**:
   - `long_rag` processed 50 long-context queries through the dedicated reasoning model (`Qwen2.5-1.5B-Instruct`).
