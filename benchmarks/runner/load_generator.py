import asyncio
import os
import sys
import time

import httpx

# Automatically add the packages directory to PYTHONPATH so it can find common.config
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "packages", "common", "src"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "packages", "contracts", "src"))

from common.config import settings


async def run_scenario(scenario_path: str):
    import yaml
    with open(scenario_path, "r") as f:
        scenario = yaml.safe_load(f)
        
    concurrency = scenario.get("concurrency", 1)
    num_requests = scenario.get("requests", 10)
    payload = scenario.get("payload")
    
    semaphore = asyncio.Semaphore(concurrency)
    
    async def make_request(client, req_id):
        async with semaphore:
            start_time = time.time()
            try:
                # We hit the gateway
                resp = await client.post(
                    f"http://localhost:{settings.gateway_port}/v1/chat/completions",
                    json=payload
                )
                duration = time.time() - start_time
                return {"status": resp.status_code, "duration": duration}
            except Exception as e:
                return {"status": 500, "duration": time.time() - start_time, "error": str(e)}

    async with httpx.AsyncClient(timeout=60.0) as client:
        start_total = time.time()
        tasks = [make_request(client, i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_total
        
        successes = [r for r in results if r["status"] == 200]
        failures = [r for r in results if r["status"] != 200]
        
        avg_latency = sum(r["duration"] for r in successes) / len(successes) if successes else 0
        rps = num_requests / total_time
        
        print(f"Scenario: {scenario['name']}")
        print(f"Total Requests: {num_requests}")
        print(f"Concurrency: {concurrency}")
        print(f"Success: {len(successes)}")
        print(f"Failures: {len(failures)}")
        print(f"Avg Latency: {avg_latency:.3f}s")
        print(f"Throughput: {rps:.2f} req/s")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    args = parser.parse_args()
    asyncio.run(run_scenario(args.scenario))
