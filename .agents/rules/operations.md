# Rule: Operations

1. Overload & Backpressure:
   - Implement overload behavior with bounded queues, timeouts, load shedding, and explicit 429 or 503 errors.
   - Do not automatically retry non-idempotent tool calls or side-effecting agent actions.
   - Use limited retries with exponential backoff and jitter for safe transient failures only.

2. Observability:
   - Use structured logs.
   - Export Prometheus metrics (e.g., latency, TTFT, token usage, cache hits).

3. Rollback & Incident Safety:
   - Require human approval for destructive actions.
   - Runbooks should be consulted during incidents.
