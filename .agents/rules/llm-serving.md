# Rule: LLM Serving & Inference Standards

1. Precise Memory Terminology:
   - KV-cache memory grows approximately linearly with token count for a fixed model architecture and precision.
   - Attention compute increases materially with context length; KV cache is a VRAM capacity constraint.
   - Never claim KV-cache memory grows quadratically.

2. Concurrency Separation:
   - Async Gateway Concurrency: Controls in-flight HTTP requests via asyncio semaphores.
   - Continuous Batching: Inference engine dynamic scheduling across decode/prefill iterations.
   - Treat these as complementary, distinct layers.

3. Prefix Caching Invariants:
   - Prefix caching requires token-identical stable prefixes.
   - Never inject volatile metadata (timestamps, UUIDs, dynamic user state) into the prefix.
   - Tools must be canonically sorted before prompt assembly.

4. Quantization & Performance Verification:
   - Do not promote quantized models based solely on throughput.
   - Always validate task success, structured JSON validity, and tool-call accuracy.
   - Never invent CLI flags, model names, or undocumented engine parameters.
