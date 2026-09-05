import asyncio
import json
import os
import sys
import time

import httpx

# Automatically add the packages directory to PYTHONPATH so it can find common.config
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "packages",
        "common",
        "src",
    )
)
sys.path.append(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "packages",
        "contracts",
        "src",
    )
)

from common.config import settings


async def run_scenario(scenario_path: str, output_path: str = None):
    import yaml

    with open(scenario_path) as f:
        scenario = yaml.safe_load(f)

    concurrency = scenario.get("concurrency", 1)
    num_requests = scenario.get("requests", 10)
    workload_type = scenario.get("workload_type", "chat")
    payload = dict(scenario.get("payload", {}))
    # Inject routing workload_type into the payload so gateway routes correctly
    payload["workload_type"] = workload_type

    semaphore = asyncio.Semaphore(concurrency)

    async def make_request(client, req_id):
        async with semaphore:
            start_time = time.time()
            try:
                resp = await client.post(
                    f"http://localhost:{settings.gateway_port}/v1/chat/completions",
                    json=payload,
                )
                duration = time.time() - start_time
                return {"status": resp.status_code, "duration": duration}
            except Exception as e:
                return {"status": 500, "duration": time.time() - start_time, "error": str(e)}

    async with httpx.AsyncClient(timeout=120.0) as client:
        start_total = time.time()
        tasks = [make_request(client, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_total

    successes = [r for r in results if r["status"] == 200]
    failures = [r for r in results if r["status"] != 200]

    durations = sorted(r["duration"] for r in successes)
    n = len(durations)

    def percentile(data, p):
        if not data:
            return 0.0
        k = int(len(data) * p / 100)
        return data[min(k, len(data) - 1)]

    avg_latency = sum(durations) / n if n else 0
    p50 = percentile(durations, 50)
    p95 = percentile(durations, 95)
    p99 = percentile(durations, 99)
    rps = num_requests / total_time if total_time > 0 else 0

    sep = "-" * 50
    print(sep)
    print(f"  Scenario   : {scenario.get('name', os.path.basename(scenario_path))}")
    print(f"  Workload   : {workload_type}")
    print(f"  Requests   : {num_requests}  (concurrency={concurrency})")
    print(f"  Success    : {len(successes)} / Failures: {len(failures)}")
    print(f"  Throughput : {rps:.2f} req/s")
    print(f"  Latency    : avg={avg_latency:.3f}s  p50={p50:.3f}s  p95={p95:.3f}s  p99={p99:.3f}s")
    if failures:
        sample = failures[:3]
        for f in sample:
            print(f"  [FAIL] status={f['status']}  err={f.get('error', '')}")
    print(sep)

    scenario_metrics = {
        "scenario": scenario.get("name", os.path.basename(scenario_path)),
        "description": scenario.get("description", ""),
        "workload_type": workload_type,
        "concurrency": concurrency,
        "requests": num_requests,
        "total_time_s": round(total_time, 4),
        "success_count": len(successes),
        "failure_count": len(failures),
        "success_rate_pct": round((len(successes) / num_requests * 100) if num_requests else 0, 2),
        "throughput_rps": round(rps, 2),
        "latency": {
            "avg_s": round(avg_latency, 4),
            "p50_s": round(p50, 4),
            "p95_s": round(p95, 4),
            "p99_s": round(p99, 4),
        },
        "failures_sample": failures[:5] if failures else [],
    }

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        existing_data = []
        if os.path.exists(output_path):
            try:
                with open(output_path, "r", encoding="utf-8") as out_f:
                    existing_data = json.load(out_f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
            except Exception:
                existing_data = []
        existing_data.append(scenario_metrics)
        with open(output_path, "w", encoding="utf-8") as out_f:
            json.dump(existing_data, out_f, indent=2)

    return scenario_metrics


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM Serving Load Generator & Benchmark Runner")
    parser.add_argument("--scenario", required=True, help="Path to scenario YAML file")
    parser.add_argument("--output", default=None, help="Optional JSON file path to append benchmark results")
    args = parser.parse_args()
    asyncio.run(run_scenario(args.scenario, output_path=args.output))

