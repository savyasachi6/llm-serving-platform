# Rule: Security, Privacy & Cache Safety

1. Secret & Data Protection:
   - Never log raw prompts, raw model completions, authorization headers, or secrets.
   - Strip all sensitive fields in structured JSON logs using opaque hashes or redaction tokens.
   - Commit only `.env.example`. Never commit `.env` or API tokens.

2. Cache Isolation:
   - Exact cache keys MUST include: `tenant_scope`, `auth_scope`, `model_id`, `system_prompt_version`, and normalized payload.
   - Semantic caching is DISABLED by default.
   - Banned from Semantic Cache: Side-effecting tool calls, personalized user data, financial/legal/medical queries, and changing external context.

3. Destructive Action Guardrails:
   - Do not pull multi-gigabyte models, start GPU containers, delete files, or modify infrastructure without explicit human confirmation.
