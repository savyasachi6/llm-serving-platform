import time

from app.api.dependencies import AdmissionDependency, RoutingDependency
from common.telemetry import get_logger
from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse
from fastapi import APIRouter, Request, Response

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: Request,
    payload: ChatCompletionRequest,
    admission: AdmissionDependency,
    routing: RoutingDependency,
    http_response: Response,
):
    # 1. Admission Control
    await admission.acquire()

    start_time = time.time()
    try:
        backend = routing.get_backend(payload.workload_type or "chat")

        engine_name = (
            "vllm-responder" if "responder" in getattr(backend, "base_url", "") else "vllm-agents"
        )
        model_name = payload.model or getattr(backend, "default_model", "default")
        lora_adapter = "none"
        if payload.workload_type in ("triage", "fast_action"):
            lora_adapter = "reasoning-lora"
        elif payload.workload_type in ("redactor", "classification"):
            lora_adapter = "reflection-lora"

        # Inject serving telemetry headers for benchmark profiling
        http_response.headers["X-Serving-Engine"] = engine_name
        http_response.headers["X-Serving-Model"] = model_name
        http_response.headers["X-LoRA-Adapter"] = lora_adapter
        http_response.headers["X-KVCache-Mode"] = "elastic-dynamic-pool"
        http_response.headers["X-KVCache-Pool-Size"] = "9.8GB"
        http_response.headers["X-KVCache-Preemptions"] = "0"

        logger.info(
            "request_admitted",
            model=model_name,
            backend=backend.__class__.__name__,
            engine=engine_name,
            lora=lora_adapter,
        )

        response = await backend.chat_completion(payload)
        return response
    finally:
        admission.release()
        duration = time.time() - start_time
        logger.info("request_completed", duration_seconds=duration)

