# LLM Serving Platform - Stress Test Benchmark Report

- **Timestamp**: 20260905_051340
- **Target Environment**: K8S
- **Total Scenarios Evaluated**: 7

## Performance Results Table

| Scenario | Concurrency | Total Req | Success Rate | Throughput (RPS) | Decode Tokens/s | TTFT p50 (ms) | TPOT p50 (ms/tok) | Latency p50 (s) | Latency p95 (s) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **cascading_compound_agent** | 8 | 48 | 75.0% | **4.39 req/s** | **131.1 tok/s** | 107.0 ms | 45.2 ms | 1.337s | 4.339s |
| **dynamic_lora_churn** | 16 | 80 | 40.0% | **14.02 req/s** | **143.7 tok/s** | 623.5 ms | 61.7 ms | 1.559s | 2.346s |
| **heterogeneous_pipeline** | 12 | 60 | 100.0% | **9.64 req/s** | **304.9 tok/s** | 468.9 ms | 51.9 ms | 1.172s | 1.831s |
| **long_rag** | 5 | 50 | 100.0% | **3.73 req/s** | **240.6 tok/s** | 612.4 ms | 19.4 ms | 1.531s | 1.985s |
| **overload** | 100 | 1000 | 100.0% | **21.07 req/s** | **509.8 tok/s** | 850.0 ms | 344.5 ms | 4.152s | 6.234s |
| **shared_prefix_agents** | 10 | 100 | 100.0% | **15.62 req/s** | **92.6 tok/s** | 45.8 ms | 108.2 ms | 0.573s | 1.034s |
| **short_chat** | 10 | 100 | 100.0% | **11.29 req/s** | **287.1 tok/s** | 258.0 ms | 35.1 ms | 0.645s | 1.960s |

## Core LLM Benchmark Metrics Reference
- **TTFT (Time To First Token)**: Prefill latency before generation starts. Noticeable drop in  due to KV-Cache reuse.
- **TPOT (Time Per Output Token)**: Decode speed per stream. Directly correlates with reading speed / user experience.
- **Decode Tokens/s**: True token generation throughput across the serving cluster.

