# Platform Threat Model

## Assumptions
- The internal network is secure, but the gateway is exposed to untrusted user input.
- LLM weights are considered trusted (pulled from official Hugging Face repositories).

## Key Threats and Mitigations

### 1. Cross-Tenant Data Leakage via Cache
- **Threat:** Tenant B receives a cached response generated for Tenant A.
- **Mitigation:** Strict tenant isolation is enforced at the **Gateway** level (not by vLLM). Before a request is processed, the Gateway constructs an exact-match cache key by generating a SHA-256 hash of a JSON payload that combines the raw prompt, `model_id`, `system_version`, and most importantly, the `tenant_scope` (which maps to the auth token). 
Because the `tenant_scope` is mathematically folded into the hash, two identical prompts from different tenants result in entirely different cache keys. This makes it impossible for Tenant B to access Tenant A's cached response. (Semantic/fuzzy caching is disabled by default for sensitive workloads to prevent accidental leakage).

### 2. Prompt Injection and Exfiltration
- **Threat:** User input tricks the LLM into leaking system prompts or executing unauthorized tools.
- **Mitigation:** Sandboxed agent execution, strict output parsing, and read-only vector stores.

### 3. Log Redaction
- **Threat:** Plaintext logs capture sensitive user queries.
- **Mitigation:** The gateway uses structlog to strip all PII and raw prompt contents before emitting metrics or logs.
