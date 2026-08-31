# Rule: Testing

1. Test Expectations:
   - Keep modules independently testable.
   - Require tests for all behavioral changes.
   - Use `pytest -q`.
   
2. Infrastructure Validation:
   - Require Compose validation after infrastructure changes using `docker compose config`.
