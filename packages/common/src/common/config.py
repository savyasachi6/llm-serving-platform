from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    gateway_port: int = 8000
    gateway_log_level: str = "INFO"
    global_agent_concurrency: int = 50
    per_backend_concurrency: int = 20
    per_workflow_concurrency: int = 10
    
    vllm_base_url: str = "http://localhost:8080/v1"
    vllm_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    
    enable_metrics: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
