from app.infrastructure.backends.base import BackendClient
from app.infrastructure.backends.mock_client import MockClient
from app.infrastructure.backends.ollama_client import OllamaClient
from app.infrastructure.backends.vllm_client import VllmClient
from common.config import settings


class RoutingService:
    def __init__(self, use_mock: bool = False):
        self.vllm_responder = MockClient() if use_mock else VllmClient(base_url=settings.vllm_responder_base_url, default_model=settings.vllm_responder_model)
        self.vllm_agents = MockClient() if use_mock else VllmClient(base_url=settings.vllm_agents_base_url, default_model=settings.vllm_agents_model)
        self.vllm = self.vllm_responder  # Alias for backward compatibility
        self.ollama = MockClient() if use_mock else OllamaClient()
        
    def get_backend(self, workload_type: str) -> BackendClient:
        # Heterogeneous Multi-Model & Multi-LoRA Routing:
        # 1. vllm-responder: Dedicated high-accuracy reasoning & synthesis node
        #    - responder: Generates empathetic, factual final email replies
        #    - reasoning: Complex multi-step reasoning / synthesis
        # 2. vllm-agents: High-speed node with Multi-LoRA dynamic hot-swapping
        #    - triage: Requests 'reasoning-lora' adapter for fast intent classification
        #    - redactor: Requests 'reflection-lora' adapter for PII security sanitization
        #    - fast_action: Low-latency classification & extraction tasks
        # 3. ollama: Local CPU fallback for dev / offline batch processing
        
        if workload_type in ("responder", "reasoning", "precision", "synthesis"):
            return self.vllm_responder
        elif workload_type in ("triage", "redactor", "throughput", "agents", "fast_action", "classification"):
            return self.vllm_agents
        elif workload_type in ("local", "cpu"):
            return self.ollama
        else:
            return self.vllm_agents # default high-throughput fallback
