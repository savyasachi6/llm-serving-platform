from fastapi import HTTPException, status
from app.infrastructure.backends.base import BackendClient
from app.infrastructure.backends.vllm_client import VllmClient
from app.infrastructure.backends.ollama_client import OllamaClient
from app.infrastructure.backends.mock_client import MockClient

class RoutingService:
    def __init__(self, use_mock: bool = False):
        self.vllm = MockClient() if use_mock else VllmClient()
        self.ollama = MockClient() if use_mock else OllamaClient()
        
    def get_backend(self, workload_type: str) -> BackendClient:
        # Default routing policy:
        # agentic -> vLLM
        # chat -> vLLM
        # shared-prefix rag -> vLLM
        # batch -> Ollama when enabled
        # local -> Ollama
        
        if workload_type in ("agentic", "chat", "rag"):
            return self.vllm
        elif workload_type in ("batch", "local"):
            return self.ollama
        else:
            return self.vllm # default fallback
