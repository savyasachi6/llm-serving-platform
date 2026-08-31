import httpx
from typing import List, Dict, Any, Optional
from common.config import settings
from contracts.openai_models import ChatCompletionResponse

class GatewayClient:
    def __init__(self):
        # Default to local gateway if not specified
        self.gateway_url = "http://localhost:8000/v1"
        self.client = httpx.AsyncClient(timeout=60.0)

    async def generate_completion(
        self, 
        messages: List[Dict[str, Any]], 
        workload_type: str, 
        max_tokens: int = 512, 
        temperature: float = 0.7,
        model: Optional[str] = "default"
    ) -> ChatCompletionResponse:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "workload_type": workload_type
        }
        
        response = await self.client.post(
            f"{self.gateway_url}/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return ChatCompletionResponse(**response.json())
