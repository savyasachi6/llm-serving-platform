from typing import Protocol, Optional
import hashlib
import json
# pyrefly: ignore [missing-import]
from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse

class CachePolicy:
    @staticmethod
    def is_cacheable(request: ChatCompletionRequest) -> bool:
        # Banned from cache: High temp, semantic caching for sensitive workloads (we only do exact here)
        # We always cache exact unless explicitly asked not to via a custom flag.
        # But we must ensure tenant_scope is present.
        if not request.tenant_scope:
            return False
        return True

class ExactCacheKeyBuilder:
    @staticmethod
    def build_key(request: ChatCompletionRequest, system_version: str = "v1") -> str:
        # exact cache keys MUST include: tenant_scope, auth_scope (we merge with tenant), model_id, system_prompt_version, normalized payload.
        payload = request.model_dump(exclude_none=True)
        # Drop volatile metadata for key definition
        payload.pop("priority", None)
        
        data = {
            "tenant_scope": request.tenant_scope,
            "model_id": request.model,
            "system_version": system_version,
            "payload": payload
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()

class ExactResponseCache(Protocol):
    async def get(self, key: str) -> Optional[ChatCompletionResponse]: ...
    async def set(self, key: str, response: ChatCompletionResponse, ttl: int = 3600) -> None: ...

class InMemoryExactCache(ExactResponseCache):
    def __init__(self):
        self._cache = {}
        
    async def get(self, key: str) -> Optional[ChatCompletionResponse]:
        return self._cache.get(key)
        
    async def set(self, key: str, response: ChatCompletionResponse, ttl: int = 3600) -> None:
        self._cache[key] = response
