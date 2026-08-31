# Rule: Architectural Boundaries & Modularity

1. Component Boundaries:
   - `apps/gateway`: Owns HTTP transport, admission, routing, timeouts, and metrics. No prompt templates or RAG business logic.
   - `apps/agent-worker`: Owns task graphs, bounded fan-out/fan-in, and agent cancellation. No HTTP server routes.
   - `packages/contracts`: Pure Pydantic DTOs. Zero dependencies on FastAPI, vLLM, or Redis.
   - `packages/prompt-engine`: Owns stable prefix layout, token budgets, and canonical tool sorting. Does not invoke model APIs.
   - `packages/retrieval`: Owns chunking, deduplication, and context budgeting. Does not touch engine flags.

2. Dependency Inversion:
   - Application layers communicate via abstract contracts.
   - Route handlers must remain thin coordinators.
