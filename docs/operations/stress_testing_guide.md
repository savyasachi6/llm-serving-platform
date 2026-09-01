# Stress Testing Guide

This guide explains how to benchmark and stress test the Cost-Efficient LLM Serving platform using the included synthetic load generation tools.

## Prerequisites

1. Ensure the Kubernetes cluster (or local KinD cluster) is running and all pods in the `default` namespace are in the `Running` state:
   ```bash
   kubectl get pods
   ```
2. Port-forward the **Gateway** service to your local machine:
   ```bash
   kubectl port-forward svc/gateway 8000:8000
   ```
   *(Keep this terminal open while running tests).*
3. Ensure you have activated your Python virtual environment where the testing scripts are located:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

## Running Benchmarks

The benchmark suite includes a load generator script that simulates concurrent client requests to the Gateway.

### Available Scenarios
All scenarios are located in `benchmarks/scenarios/`.

*   `short_chat.yaml`: Baseline short multi-turn chat to test standard throughput.
*   `shared_prefix_agents.yaml`: Tests prefix-caching gain using a shared system prompt.
*   `long_rag.yaml`: Tests chunked prefill performance.
*   `overload.yaml`: Saturation test to verify admission rejection (HTTP 429/503) and graceful recovery under extreme load.

### Executing a Scenario

To run a scenario, use the `load_generator.py` script:

```bash
python benchmarks/runner/load_generator.py --scenario benchmarks/scenarios/short_chat.yaml
```

The script will output metrics including:
*   Total Requests
*   Concurrency
*   Success/Failure counts
*   Average Latency
*   Throughput (Requests per second)

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
