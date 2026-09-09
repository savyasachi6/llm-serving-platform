# 6. Speculative Decoding

## Concept
Speculative decoding accelerates text generation by using a small, fast "draft" model to propose several candidate tokens simultaneously. The larger "target" model then verifies these candidates in a single forward pass. Since verifying multiple tokens in parallel costs roughly the same as verifying one, this can massively increase decode tokens-per-second.

## Constraints & Implementation Rules
- **Disabled by Default:** Do not enable speculative decoding by default. The architectural coordination overhead often outweighs the gains for short, latency-critical, or single-token classification prompts.
- **Interface First:** Always design the interface and use a feature flag before enabling it. It requires verified engine support, compatible model artifacts, and adequate GPU memory.
- **No Fabricated Artifacts:** Do not blindly fabricate EAGLE, Medusa, or arbitrary draft-model artifacts without explicitly validating their compatibility and accuracy.

## Implementation Details
- Speculative decoding is disabled by default in our configuration (`infra/vllm/speculative/draft_model_config.yaml`).
- It is strictly an opt-in optimization reserved for workloads where long-form generation dominates the token budget.
