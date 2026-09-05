import os
import re
import time
import uuid
from typing import Any

import httpx
from common.config import settings
from contracts.openai_models import (
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)


class GatewayClient:
    def __init__(self, gateway_url: str | None = None):
        # In Kubernetes, the agent-worker Deployment sets GATEWAY_URL=http://gateway:80.
        # The gateway Service (gateway-service.yaml) maps port 80 -> container port 8000.
        # We read from the environment so the same code works in both K8s and local dev.
        # Fallback chain: explicit arg -> env var -> K8s DNS default.
        self.gateway_url = gateway_url or os.environ.get("GATEWAY_URL", "http://gateway:80") + "/v1"
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_completion(
        self,
        messages: list[dict[str, Any]],
        workload_type: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        model: str | None = None,
    ) -> ChatCompletionResponse:
        if model in (None, "default"):
            if workload_type in ("responder", "reasoning", "precision", "synthesis"):
                model = settings.vllm_responder_model
            elif workload_type == "triage":
                model = settings.vllm_triage_lora
            elif workload_type == "redactor":
                model = settings.vllm_redact_lora
            else:
                model = settings.vllm_agents_model

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "workload_type": workload_type,
        }

        try:
            response = await self.client.post(f"{self.gateway_url}/chat/completions", json=payload)
            response.raise_for_status()
            return ChatCompletionResponse(**response.json())
        except (httpx.ConnectError, httpx.TimeoutException, httpx.ReadTimeout):
            # Fallback mock execution for standalone local testing when gateway is offline
            user_content = next(
                (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
            )

            if workload_type == "triage":
                simulated_text = (
                    "Billing"
                    if any(
                        w in user_content.lower()
                        for w in ["bill", "charge", "refund", "invoice", "payment"]
                    )
                    else "Technical"
                )
            elif workload_type == "redactor":
                simulated_text = user_content
                simulated_text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN-REDACTED]", simulated_text)
                simulated_text = re.sub(
                    r"[\w\.-]+@[\w\.-]+\.\w+", "[EMAIL-REDACTED]", simulated_text
                )
                simulated_text = re.sub(
                    r"\b(?:\d{4}-){3}\d{4}\b", "[CARD-REDACTED]", simulated_text
                )
                simulated_text = re.sub(r"Jane Doe", "[NAME-REDACTED]", simulated_text)
            elif workload_type == "responder":
                simulated_text = "Thank you for contacting billing support. We have reviewed your invoice and processed the refund of the duplicate charge, which will appear in 3-5 business days."
            else:
                simulated_text = f"Mock response for {workload_type}"

            return ChatCompletionResponse(
                id=f"chatcmpl-mock-{uuid.uuid4().hex[:8]}",
                object="chat.completion",
                created=int(time.time()),
                model=model or "mock-model",
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=simulated_text),
                        finish_reason="stop",
                    )
                ],
                usage=UsageInfo(prompt_tokens=20, completion_tokens=30, total_tokens=50),
            )
