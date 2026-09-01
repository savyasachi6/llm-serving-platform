from app.infrastructure.backends.base import BackendClient
from app.infrastructure.backends.mock_client import MockClient
from app.infrastructure.backends.ollama_client import OllamaClient
from app.infrastructure.backends.vllm_client import VllmClient
from common.config import settings


class RoutingService:
    def __init__(self, use_mock: bool = False):
        self.vllm_precision = MockClient() if use_mock else VllmClient(base_url=settings.vllm_precision_base_url)
        self.vllm_throughput = MockClient() if use_mock else VllmClient(base_url=settings.vllm_throughput_base_url)
        self.vllm = self.vllm_precision  # Alias for backward compatibility
        self.ollama = MockClient() if use_mock else OllamaClient()
        
    def get_backend(self, workload_type: str) -> BackendClient:
        # Heterogeneous Multi-Model & Multi-LoRA Routing:
        # 1. vllm-precision: Dedicated high-accuracy reasoning & synthesis node
        #    - responder: Generates empathetic, factual final email replies
        #    - reasoning: Complex multi-step reasoning / synthesis
        # 2. vllm-throughput: High-speed node with Multi-LoRA dynamic hot-swapping
        #    - triage: Requests 'reasoning-lora' adapter for fast intent classification
        #    - redactor: Requests 'reflection-lora' adapter for PII security sanitization
        #    - fast_action: Low-latency classification & extraction tasks
        # 3. ollama: Local CPU fallback for dev / offline batch processing
        
        if workload_type in ("responder", "reasoning", "precision", "synthesis"):
            return self.vllm_precision
        elif workload_type in ("triage", "redactor", "throughput", "fast_action", "classification"):
            return self.vllm_throughput
        elif workload_type in ("local", "cpu"):
            return self.ollama
        else:
            return self.vllm_throughput # default high-throughput fallback
