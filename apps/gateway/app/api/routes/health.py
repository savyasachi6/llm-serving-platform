from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class HealthResponse(BaseModel):
    status: str

@router.get("/healthz", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="ok")

@router.get("/readyz", response_model=HealthResponse)
async def ready_check():
    return HealthResponse(status="ready")
