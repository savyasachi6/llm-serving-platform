import pytest
from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse

def test_openai_request_contract():
    # Validates that our internal representation can successfully serialize
    # to the standard OpenAI JSON format.
    req = ChatCompletionRequest(
        model="test-model",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.7
    )
    
    data = req.model_dump(exclude_none=True)
    assert "model" in data
    assert "messages" in data
    assert "temperature" in data
    
    # Custom fields should be present
    assert "workload_type" in data
    
    # But we drop them when forwarding to real backends (handled in client)
    forward_data = req.model_dump(exclude_none=True, exclude={"workload_type", "priority", "cache_key", "tenant_scope"})
    assert "workload_type" not in forward_data

def test_openai_response_contract():
    resp_json = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hi there"
                },
                "finish_reason": "stop"
            }
        ]
    }
    
    resp = ChatCompletionResponse(**resp_json)
    assert resp.id == "chatcmpl-123"
    assert resp.choices[0].message.content == "Hi there"
