# Stress Testing Guide

This guide explains how to benchmark and stress test the Cost-Efficient LLM Serving platform using the included synthetic load generation tools.

## Automated All-in-One Benchmark Runner

We provide an automated, all-in-one bash runner that performs pre-flight environment checks, automatically launches the serving stack (on Kubernetes/Minikube or Docker Compose), verifies Gateway readiness, runs all scenarios sequentially, and collects structured benchmark metrics.

```bash
# Run all-in-one stress test suite against Kubernetes (Minikube):
bash scripts/run_stress_tests.sh --target k8s

# Or test against Docker Compose:
bash scripts/run_stress_tests.sh --target compose
```

### Automatic Benchmark Collection
Every run collects and saves comprehensive benchmark outputs under `benchmarks/results/`:
- **Markdown Report**: `benchmarks/results/stress_test_<timestamp>.md` (and `latest_report.md`)
- **Structured JSON Metrics**: `benchmarks/results/stress_test_<timestamp>.json` (and `latest_metrics.json`)
- **Raw Execution Log**: `benchmarks/results/stress_test_<timestamp>.log`

The report includes concurrency, total requests, success rates, throughput (RPS), and latency percentiles (avg, p50, p95, p99).

---

## Manual Execution (Individual Scenarios)

If you prefer to run individual scenarios manually:

1. Ensure the serving stack is running and healthy:
   ```bash
   curl http://localhost:8000/healthz
   ```
2. Run a specific scenario using `load_generator.py` and optionally save the collected metrics:
   ```bash
   uv run python benchmarks/runner/load_generator.py \
       --scenario benchmarks/scenarios/short_chat.yaml \
       --output benchmarks/results/manual_run.json
   ```

### Available Scenarios
All scenarios are located in `benchmarks/scenarios/`:
* `short_chat.yaml`: Baseline short multi-turn chat to test standard throughput.
* `shared_prefix_agents.yaml`: Tests prefix-caching gain using a shared system prompt.
* `long_rag.yaml`: Tests chunked prefill performance.
* `overload.yaml`: Saturation test to verify admission rejection (HTTP 429) and graceful recovery under extreme load.


## Monitoring with Grafana

During the stress test, you can monitor live cluster performance using the bundled Prometheus and Grafana stack.

1. Port-forward Grafana:
   ```bash
   # We use port 3001 locally to avoid conflict with the frontend playground on port 3000
   kubectl port-forward svc/grafana 3001:3000
   ```
2. Open your browser to [http://localhost:3001](http://localhost:3001).
3. Log in with credentials: `admin` / `admin`.
4. Open the **LLM Serving Dashboard** to view live metrics on:
   *   Gateway Latency per Tenant/Model
   *   Cache Hit Rates
   *   Request Throughput (QPS)
   *   vLLM Engine GPU Memory/KV Cache usage (if running in GPU mode)
