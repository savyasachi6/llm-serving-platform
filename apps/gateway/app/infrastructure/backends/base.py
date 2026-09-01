from typing import Protocol

from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse


class BackendClient(Protocol):
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        ...
    
    async def is_healthy(self) -> bool:
        ...
