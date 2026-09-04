import pytest
from app.api.dependencies import get_routing_service
from app.application.routing_service import RoutingService
from app.main import app
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def override_routing():
    app.dependency_overrides[get_routing_service] = lambda: RoutingService(use_mock=True)
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_ready_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/readyz")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}

@pytest.mark.asyncio
async def test_chat_completions_mock():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "hello"}],
            "workload_type": "chat"
        }
        response = await client.post("/v1/chat/completions", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "test-model"
        assert len(data["choices"]) == 1
        assert data["choices"][0]["message"]["content"] == "This is a mock response."

@pytest.mark.asyncio
async def test_heterogeneous_workload_routing():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for workload in ["responder", "triage", "redactor", "local", "reasoning"]:
            payload = {
                "model": "llama-3.2-3b",
                "messages": [{"role": "user", "content": f"test {workload}"}],
                "workload_type": workload
            }
            response = await client.post("/v1/chat/completions", json=payload)
            assert response.status_code == 200
            assert response.json()["choices"][0]["message"]["content"] == "This is a mock response."

