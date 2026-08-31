from fastapi import APIRouter, HTTPException, Request
from contracts.openai_models import ChatCompletionRequest, ChatCompletionResponse
from app.api.dependencies import AdmissionDependency, RoutingDependency
from common.telemetry import get_logger
import time

router = APIRouter()
logger = get_logger(__name__)

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: Request,
    payload: ChatCompletionRequest,
    admission: AdmissionDependency,
    routing: RoutingDependency
):
    # 1. Admission Control
    await admission.acquire()
    
    start_time = time.time()
    try:
        backend = routing.get_backend(payload.workload_type or "chat")
        
        logger.info("request_admitted", model=payload.model, backend=backend.__class__.__name__)
        
        response = await backend.chat_completion(payload)
        return response
    finally:
        admission.release()
        duration = time.time() - start_time
        logger.info("request_completed", duration_seconds=duration)
