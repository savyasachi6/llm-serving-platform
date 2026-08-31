# Platform Threat Model

## Assumptions
- The internal network is secure, but the gateway is exposed to untrusted user input.
- LLM weights are considered trusted (pulled from official Hugging Face repositories).

## Key Threats and Mitigations

### 1. Cross-Tenant Data Leakage via Cache
- **Threat:** Tenant B receives a cached response generated for Tenant A.
- **Mitigation:** Cache keys cryptographically enforce `tenant_scope` and `auth_scope`. Semantic caching is disabled by default.

### 2. Prompt Injection and Exfiltration
- **Threat:** User input tricks the LLM into leaking system prompts or executing unauthorized tools.
- **Mitigation:** Sandboxed agent execution, strict output parsing, and read-only vector stores.

### 3. Log Redaction
- **Threat:** Plaintext logs capture sensitive user queries.
- **Mitigation:** The gateway uses structlog to strip all PII and raw prompt contents before emitting metrics or logs.
