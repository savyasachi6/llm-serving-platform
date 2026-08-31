# Platform Architecture Overview

## The Big Picture

The `agentic-llm-serving-platform` is designed to be a high-throughput, cost-efficient inference layer. It acts as the bridge between your end-user applications and the underlying Large Language Models (LLMs).

### Core Components

1. **Gateway (`apps/gateway`)**
   - **Role:** The front door of the platform.
   - **Responsibilities:** Receives HTTP requests, performs admission control (to prevent overloading the system), enforces token/request timeouts, and routes requests to the appropriate backend model.
   - **Caching:** Uses exact-match caching (respecting tenant boundaries) to serve repeated queries instantly without hitting the expensive LLMs.

2. **Agent Worker (`apps/agent-worker`)**
   - **Role:** The orchestrator for complex, multi-step LLM tasks.
   - **Responsibilities:** Manages "Task Graphs". When an AI agent needs to perform a multi-step workflow (e.g., search the web, read a document, then summarize), the worker manages these steps, handles fan-out (running things in parallel), and safely cancels operations if a parent task fails.

3. **Inference Engines (The Backends)**
   - **vLLM:** The primary workhorse. It is a highly optimized inference engine that uses PagedAttention and Prefix Caching. It is used for heavy, concurrent production workloads (like chat and agentic loops).
   - **Ollama:** The fallback/local engine. It is extremely easy to run locally and supports highly quantized models (GGUF). It is used for offline batch processing or local development when you don't have massive GPU resources.

4. **Shared Packages (`packages/`)**
   - Contains reusable logic that both the Gateway and the Agent Worker share, such as:
     - `contracts`: The exact data shapes (Pydantic models) used to communicate.
     - `prompt-engine`: Logic for assembling prompts in a highly deterministic way, which is crucial for maximizing prefix-cache hits in vLLM.
     - `retrieval`: Logic for safely budgeting context limits when doing RAG (Retrieval-Augmented Generation).

## How a Request Flows

1. A user asks a question.
2. The request hits the **Gateway**.
3. The Gateway checks the **Cache**. If it's a hit, it returns the answer immediately.
4. If it's a miss, the Gateway checks its **Admission Control** semaphore. If the system is too busy, it rejects the request early (HTTP 503) rather than letting it hang forever.
5. If admitted, the **Routing Service** looks at the `workload_type` (e.g., `chat` vs `batch`) and forwards the request to either **vLLM** or **Ollama**.
6. The engine streams the response back through the Gateway to the user.
