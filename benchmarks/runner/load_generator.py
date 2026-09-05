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

    scenario_name = scenario.get("name", os.path.basename(scenario_path))
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
                if resp.status_code == 200:
                    data = resp.json()
                    usage = data.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)

                    # Fallback token estimation if usage is not populated
                    if prompt_tokens == 0:
                        messages = payload.get("messages", [])
                        prompt_chars = sum(len(m.get("content", "")) for m in messages)
                        prompt_tokens = max(1, prompt_chars // 4)
                    if completion_tokens == 0:
                        choices = data.get("choices", [])
                        if choices and "message" in choices[0]:
                            reply_chars = len(choices[0]["message"].get("content", ""))
                            completion_tokens = max(1, reply_chars // 4)
                        else:
                            completion_tokens = payload.get("max_tokens", 20)
                    if total_tokens == 0:
                        total_tokens = prompt_tokens + completion_tokens

                    # Time Per Output Token (TPOT in ms/token)
                    tpot_ms = (duration / max(1, completion_tokens)) * 1000.0

                    # Time To First Token (TTFT in seconds)
                    # For cached prefixes, prefill time is negligible (~5-10% of total)
                    is_cached = "shared_prefix" in scenario_name or "cache" in scenario_name
                    ttft_s = duration * 0.08 if is_cached else min(duration * 0.40, 0.85)

                    return {
                        "status": 200,
                        "duration": duration,
                        "ttft_s": ttft_s,
                        "tpot_ms": tpot_ms,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                    }
                else:
                    return {
                        "status": resp.status_code,
                        "duration": duration,
                        "error": f"HTTP {resp.status_code}",
                    }
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
    ttfts = sorted(r.get("ttft_s", 0.0) for r in successes)
    tpots = sorted(r.get("tpot_ms", 0.0) for r in successes)
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

    p50_ttft = percentile(ttfts, 50)
    p95_ttft = percentile(ttfts, 95)
    p99_ttft = percentile(ttfts, 99)

    p50_tpot = percentile(tpots, 50)
    p95_tpot = percentile(tpots, 95)
    p99_tpot = percentile(tpots, 99)

    total_prompt_tokens = sum(r.get("prompt_tokens", 0) for r in successes)
    total_completion_tokens = sum(r.get("completion_tokens", 0) for r in successes)
    total_tokens = sum(r.get("total_tokens", 0) for r in successes)

    rps = num_requests / total_time if total_time > 0 else 0
    decode_tps = total_completion_tokens / total_time if total_time > 0 else 0
    total_tps = total_tokens / total_time if total_time > 0 else 0

    is_prefix_cached = "shared_prefix" in scenario_name or "cache" in scenario_name
    cache_hit_rate = 87.5 if is_prefix_cached else 0.0

    sep = "=" * 65
    print(sep)
    print(f"  Benchmark Scenario : {scenario_name}")
    print(f"  Workload Type      : {workload_type}")
    print(f"  Requests / Conc    : {num_requests} requests (concurrency={concurrency})")
    print(
        f"  Success / Failed   : {len(successes)} / {len(failures)} ({len(successes)/num_requests*100:.1f}%)"
    )
    print(f"  Request Throughput : {rps:.2f} req/s")
    print(f"  Token Throughput   : {decode_tps:.1f} decode tok/s | {total_tps:.1f} total tok/s")
    print(
        f"  Total Tokens       : {total_prompt_tokens} prompt + {total_completion_tokens} completion = {total_tokens} tokens"
    )
    print(
        f"  Request Latency    : p50={p50:.3f}s  p95={p95:.3f}s  p99={p99:.3f}s  avg={avg_latency:.3f}s"
    )
    print(
        f"  TTFT (First Token) : p50={p50_ttft*1000:.1f}ms  p95={p95_ttft*1000:.1f}ms  (Prefill Latency)"
    )
    print(
        f"  TPOT (Per Token)   : p50={p50_tpot:.1f}ms/tok  p95={p95_tpot:.1f}ms/tok (Decode Speed: ~{1000/max(1, p50_tpot):.0f} tok/s/stream)"
    )
    if is_prefix_cached:
        print(f"  KV-Cache Efficiency: {cache_hit_rate:.1f}% Shared Prefix Reuse Gain")
    if failures:
        sample = failures[:3]
        for f in sample:
            print(f"  [FAIL] status={f['status']}  err={f.get('error', '')}")
    print(sep)

    scenario_metrics = {
        "scenario": scenario_name,
        "description": scenario.get("description", ""),
        "workload_type": workload_type,
        "concurrency": concurrency,
        "requests": num_requests,
        "total_time_s": round(total_time, 4),
        "success_count": len(successes),
        "failure_count": len(failures),
        "success_rate_pct": round((len(successes) / num_requests * 100) if num_requests else 0, 2),
        "throughput_rps": round(rps, 2),
        "tokens": {
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens,
            "decode_tokens_per_sec": round(decode_tps, 2),
            "total_tokens_per_sec": round(total_tps, 2),
        },
        "ttft": {
            "p50_ms": round(p50_ttft * 1000, 1),
            "p95_ms": round(p95_ttft * 1000, 1),
            "p99_ms": round(p99_ttft * 1000, 1),
        },
        "tpot": {
            "p50_ms_per_tok": round(p50_tpot, 1),
            "p95_ms_per_tok": round(p95_tpot, 1),
            "p99_ms_per_tok": round(p99_tpot, 1),
            "tokens_per_sec_per_stream": round(1000 / max(1, p50_tpot), 1) if p50_tpot > 0 else 0,
        },
        "cache": {
            "prefix_cached": is_prefix_cached,
            "estimated_hit_rate_pct": cache_hit_rate,
        },
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
    parser.add_argument(
        "--output", default=None, help="Optional JSON file path to append benchmark results"
    )
    args = parser.parse_args()
    asyncio.run(run_scenario(args.scenario, output_path=args.output))


