from prometheus_client import Counter, Histogram

# Metrics definition
GATEWAY_REQUESTS = Counter(
    "gateway_requests_total",
    "Total requests received by the gateway",
    ["tenant", "model", "status"],
)

GATEWAY_LATENCY = Histogram(
    "gateway_request_latency_seconds", "Latency of gateway requests", ["tenant", "model"]
)

GATEWAY_INFLIGHT = Counter("gateway_inflight_requests", "Currently in-flight requests", ["backend"])


def record_request_metrics(tenant: str, model: str, status: str, latency: float):
    """Utility to record metrics for a request lifecycle."""
    GATEWAY_REQUESTS.labels(tenant=tenant, model=model, status=status).inc()
    GATEWAY_LATENCY.labels(tenant=tenant, model=model).observe(latency)
