# 1. KV-Cache Memory

## Concept
The Key-Value (KV) cache stores the precomputed key and value tensors from the attention layers for all previously processed tokens. Instead of recalculating the attention over the entire sequence at every token generation step, the model reuses these tensors.

## Constraints & Implementation Rules
- **Linear Growth:** KV-cache memory grows approximately linearly with the number of cached tokens for a fixed model architecture and precision.
- **Never claim quadratic growth for KV cache memory.** It is the *attention computation* time complexity that scales quadratically ($O(N^2)$), not the memory footprint of the KV cache itself.
- **Dependencies:** The memory footprint depends heavily on the number of layers, KV heads, head dimension, data type, sequence count, and token count.

## Implementation Details
In our architecture, the KV cache is actively pooled and shared across instances:
- The `kvcached` daemon pre-allocates GPU VRAM and exposes it via a Unix socket (`/tmp/kvcached-ipc/kvcached.sock`).
- Inference engines (e.g., `vllm-responder` and `vllm-agents`) request memory dynamically from `kvcached`, allowing for zero-copy sharing and elastic sequence lengths without out-of-memory (OOM) crashes under heavy concurrency.
