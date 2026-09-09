# 2. Request Concurrency

## Concept
Handling massive traffic spikes efficiently requires distinct mechanisms at the networking/admission layer versus the GPU inference layer. 

## Constraints & Implementation Rules
It is critical to distinguish between and correctly configure these two complementary but distinct mechanisms:

### 1. Async Gateway Concurrency
- **Definition:** Controls how many HTTP requests can be "in flight" across the system at once.
- **Mechanism:** Implemented via asyncio semaphores at the FastAPI Gateway layer to enforce token bucket backpressure. 
- **Purpose:** Prevents downstream queuing overload and ensures zero 504 Timeouts by rejecting traffic cleanly (HTTP 429/503) when saturated.

### 2. Continuous Batching
- **Definition:** The inference engine dynamically schedules requests into GPU-efficient decode/prefill batches on a per-token basis.
- **Mechanism:** Managed entirely by the backend engine (e.g., vLLM). It dynamically swaps in new requests as old ones finish without waiting for a fixed batch to complete.
- **Purpose:** Maximizes GPU token throughput (tokens per second) and minimizes compute starvation.

## Implementation Details
- The Gateway uses configuration flags such as `GLOBAL_AGENT_CONCURRENCY` and `PER_BACKEND_CONCURRENCY` to control async gateway limits.
- The `vLLM` engines handle Continuous Batching internally via paged attention.
- **Rule:** Never confuse the two. `max_num_seqs` in vLLM controls continuous batching limits, while Gateway semaphores control the ingress async concurrency.
