# Rule: Coding Standards

1. Language and Formatting:
   - Python 3.12+ required.
   - Use `uv` for dependency management.
   - Format with `ruff`.

2. Typing:
   - Use strict Python typing throughout.
   - Use Pydantic v2 for all API contracts and settings.

3. Logging:
   - Use structured logs and correlation IDs for all requests and agent tasks.
   - Do not log raw prompts, model responses, secrets, or PII.

4. Dependency Management:
   - Keep modules independently testable.
   - Use dependency inversion at integration boundaries.
