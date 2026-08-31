import asyncio
from fastapi import HTTPException, status
from pydantic import BaseModel
from common.config import settings

class AdmissionService:
    def __init__(self):
        self.global_semaphore = asyncio.Semaphore(settings.global_agent_concurrency)
        
    async def acquire(self, timeout: float = 5.0):
        try:
            # Try to acquire with a small timeout to allow shedding load if full
            await asyncio.wait_for(self.global_semaphore.acquire(), timeout=timeout)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Server is overloaded (admission control limit reached)"
            )
            
    def release(self):
        self.global_semaphore.release()
