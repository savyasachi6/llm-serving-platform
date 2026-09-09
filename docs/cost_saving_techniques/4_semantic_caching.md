# 4. Semantic Response Caching

## Concept
Semantic response caching aims to intercept incoming user requests and return previously generated textual outputs for "similar" or identical prompts, bypassing the LLM entirely.

## Constraints & Implementation Rules
- **Hallucination Risk:** Semantic (fuzzy) caching may return a plausible but structurally or factually incorrect answer for the specific context of a new user.
- **Strictly Disabled by Default:** Never use semantic caching by default for sensitive, personalized, stateful, factual, financial, legal, medical, security, or side-effecting agent workflows.
- **Isolation:** Any cache implementation must be strongly isolated by `tenant_scope`, authorization scope, model version, prompt version, retrieval corpus version, and policy version.

## Implementation Details
- By design, we use an **Exact-Match Cache**, not a semantic cache, for the Gateway. 
- The cache key is constructed in `apps/gateway/app/infrastructure/cache/exact_cache.py` using a strict SHA-256 hash of the JSON payload combined with the `tenant_scope`. This mathematical folding guarantees that two identical prompts from different tenants result in entirely different cache keys, preventing cross-tenant data leakage.
