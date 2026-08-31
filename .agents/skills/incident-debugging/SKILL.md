---
name: incident-debugging
description: Triage and resolve production issues including queue saturation, latency spikes, engine OOMs, and 504 gateway timeouts.
---

# Skill: Incident Debugging

## Purpose
Triage and resolve production issues including queue saturation, latency spikes, engine OOMs, and 504 gateway timeouts.

## Diagnostic Workflow
1. **504 Gateway Timeouts:**
   - Inspect `gateway_inflight_requests` vs `gateway_queue_wait_seconds`.
   - Check if backend semaphore is saturated or if upstream engine is pre-empting sequences.
2. **GPU Out-of-Memory (OOM):**
   - Check `gpu_memory_utilization` setting.
   - Verify if concurrent long-context requests exceeded reserved KV cache space.
3. **Prefix Cache Miss Regressions:**
   - Verify prompt ordering via `PromptBuilder`.
   - Check if volatile metadata (timestamps, session IDs) leaked into the prefix.
4. **Agent Worker Fan-Out Freezes:**
   - Check per-workflow semaphore limits.
   - Ensure cancellation tokens propagated across failing child tasks.

## Validation Commands
```bash
curl http://localhost:8000/metrics | grep gateway_
pytest apps/gateway/tests/unit/test_admission.py
```
