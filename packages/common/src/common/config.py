from typing import Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gateway_port: int = 8000
    gateway_log_level: str = "INFO"
    global_agent_concurrency: int = 50
    per_backend_concurrency: int = 20
    per_workflow_concurrency: int = 10
    
    # vLLM base URLs for heterogeneous multi-model serving:
    # vllm-precision: Dedicated high-accuracy reasoning & synthesis node
    vllm_precision_base_url: str = "http://vllm-precision:8080/v1"
    # vllm-throughput: High-speed node with Multi-LoRA dynamic hot-swapping
    vllm_throughput_base_url: str = "http://vllm-throughput:8080/v1"
    # Legacy / single vLLM fallback base URL:
    vllm_base_url: str = "http://vllm:8080/v1"
    
    # Ollama base URL: In K8s, resolves to the ollama Service. For local dev, override
    # via .env file with OLLAMA_BASE_URL=http://localhost:11434
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "llama3:8b"
    
    enable_metrics: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("gateway_port", mode="before")
    @classmethod
    def parse_gateway_port(cls, v: Union[int, str]) -> int:
        if isinstance(v, str):
            if v.startswith("tcp://"):
                # Extract port from tcp://IP:PORT format injected by Kubernetes service link
                return int(v.split(":")[-1])
            return int(v)
        return v

settings = Settings()
