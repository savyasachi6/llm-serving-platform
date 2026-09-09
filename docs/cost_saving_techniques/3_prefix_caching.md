# 3. Prefix Caching

## Concept
Prefix caching (or Radix Prefix Caching) allows the inference engine to reuse precomputed KV states for identical token prefixes across different requests. This reduces Time-to-First-Token (TTFT) by bypassing prefill computation entirely for the shared portion of the prompt.

## Constraints & Implementation Rules
- **Stable Token Identicality:** Prefix caching *only* works reliably when the prefix is completely stable and bit-for-bit token-identical.
- **Volatile Metadata:** Never inject dynamic timestamps, random UUIDs, reordered tools, or user-specific conversational state into the shared prefix. Doing so dramatically reduces or eliminates the cache-hit rate.
- **Not Semantic Caching:** Do not confuse prefix caching (KV state reuse) with caching final textual responses (Semantic Caching).

## Implementation Details
- The `packages/prompt-engine` module owns the stable prefix layout, token budgets, and canonical tool sorting. It ensures that system instructions and tool schemas are deterministically alphabetized to maintain exact token sequences.
- We enable this via `--enable-prefix-caching` on our vLLM backend containers.
- We monitor the `vllm:gpu_prefix_cache_hit_rate` metric to ensure our prompt assembly strategy remains optimal.
