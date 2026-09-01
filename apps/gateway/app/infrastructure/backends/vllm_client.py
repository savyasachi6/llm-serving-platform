import httpx
from app.infrastructure.backends.base import BackendClient
from app.lifespan import get_http_client
from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse
from fastapi import HTTPException, status


class VllmClient(BackendClient):
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        client = get_http_client()
        try:
            # We enforce standard openai contract mapped to vLLM's implementation
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=request.model_dump(exclude_none=True, exclude={"workload_type", "priority", "cache_key", "tenant_scope"})
            )
            response.raise_for_status()
            return ChatCompletionResponse(**response.json())
        except httpx.TimeoutException:
            raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail="vLLM timeout")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="vLLM overloaded")
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"vLLM error: {e.response.text}")
            
    async def is_healthy(self) -> bool:
        client = get_http_client()
        try:
            resp = await client.get(f"{self.base_url}/models")
            return resp.status_code == 200
        except Exception:
            return False
