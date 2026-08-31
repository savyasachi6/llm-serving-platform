import time
import uuid
from app.infrastructure.backends.base import BackendClient
from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse, ChatCompletionResponseChoice, ChatMessage, UsageInfo

class MockClient(BackendClient):
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        
    async def chat_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        if self.should_fail:
            raise Exception("Mock backend failure")
            
        return ChatCompletionResponse(
            id=f"chatcmpl-mock-{uuid.uuid4().hex[:8]}",
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content="This is a mock response."),
                    finish_reason="stop"
                )
            ],
            usage=UsageInfo(prompt_tokens=10, completion_tokens=10, total_tokens=20)
        )
        
    async def is_healthy(self) -> bool:
        return not self.should_fail
