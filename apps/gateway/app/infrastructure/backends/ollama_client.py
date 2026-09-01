import httpx
from app.infrastructure.backends.base import BackendClient
from app.lifespan import get_http_client
from common.config import settings
from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse
from fastapi import HTTPException, status


class OllamaClient(BackendClient):
    def __init__(self):
        self.base_url = settings.ollama_base_url
        
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        client = get_http_client()
        try:
            # Ollama supports a somewhat OpenAI compatible endpoint at /v1/chat/completions
            response = await client.post(
                f"{self.base_url}/v1/chat/completions",
                json=request.model_dump(exclude_none=True, exclude={"workload_type", "priority", "cache_key", "tenant_scope"})
            )
            response.raise_for_status()
            return ChatCompletionResponse(**response.json())
        except httpx.TimeoutException:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="Ollama timeout")
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Ollama error: {e.response.text}")
            
    async def is_healthy(self) -> bool:
        client = get_http_client()
        try:
            resp = await client.get(f"{self.base_url}/api/tags")
            return resp.status_code == 200
        except Exception:
            return False
