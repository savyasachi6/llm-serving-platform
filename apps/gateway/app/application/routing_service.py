from fastapi import HTTPException, status
from app.infrastructure.backends.base import BackendClient
from app.infrastructure.backends.vllm_client import VllmClient
from app.infrastructure.backends.ollama_client import OllamaClient
from app.infrastructure.backends.mock_client import MockClient

from common.config import settings

class RoutingService:
    def __init__(self, use_mock: bool = False):
        self.vllm_precision = MockClient() if use_mock else VllmClient(base_url=settings.vllm_precision_url)
        self.vllm_throughput = MockClient() if use_mock else VllmClient(base_url=settings.vllm_throughput_url)
        self.ollama = MockClient() if use_mock else OllamaClient()
        
    def get_backend(self, workload_type: str) -> BackendClient:
        # Multi-LoRA Routing (Llama-3.2-3B hosts the adapters)
        # triage -> vLLM Throughput (requests reasoning-lora)
        # redactor -> vLLM Throughput (requests reflection-lora)
        # responder -> vLLM Precision (uses base Gemma-2B)
        
        if workload_type == "responder":
            return self.vllm_precision
        elif workload_type in ("triage", "redactor"):
            return self.vllm_throughput
        elif workload_type == "local":
            return self.ollama
        else:
            return self.vllm_throughput # default fallback to cheaper model
