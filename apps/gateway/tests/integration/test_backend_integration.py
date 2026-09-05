import pytest
from app.infrastructure.backends.mock_client import MockClient
from contracts.openai_models import ChatCompletionRequest


@pytest.mark.asyncio
async def test_mock_backend_integration():
    client = MockClient()
    req = ChatCompletionRequest(model="test-model", messages=[{"role": "user", "content": "hello"}])

    resp = await client.chat_completion(req)
    assert resp.model == "test-model"
    assert len(resp.choices) == 1

    assert await client.is_healthy()


@pytest.mark.asyncio
async def test_mock_backend_failure_integration():
    client = MockClient(should_fail=True)
    req = ChatCompletionRequest(model="test-model", messages=[{"role": "user", "content": "hello"}])

    with pytest.raises(Exception):
        await client.chat_completion(req)

    assert not await client.is_healthy()
