from fastapi import HTTPException, status
from app.infrastructure.backends.base import BackendClient
from app.infrastructure.backends.vllm_client import VllmClient
from app.infrastructure.backends.ollama_client import OllamaClient
from app.infrastructure.backends.mock_client import MockClient

from common.config import settings

class RoutingService:
    def __init__(self, use_mock: bool = False):
        self.vllm = MockClient() if use_mock else VllmClient(base_url=settings.vllm_base_url)
        self.ollama = MockClient() if use_mock else OllamaClient()
        
    def get_backend(self, workload_type: str) -> BackendClient:
        # Multi-LoRA Routing (Llama-3.2-3B hosts the adapters)
        # triage -> vLLM (requests reasoning-lora)
        # redactor -> vLLM (requests reflection-lora)
        # responder -> vLLM (uses base Llama-3.2-3B)
        
        if workload_type in ("responder", "triage", "redactor"):
            return self.vllm
        elif workload_type == "local":
            return self.ollama
        else:
            return self.vllm # default fallback
