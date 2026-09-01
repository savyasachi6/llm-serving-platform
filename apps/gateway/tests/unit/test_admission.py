import asyncio

import pytest
from app.application.admission_service import AdmissionService
from common.config import settings
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_admission_service_acquires_and_releases():
    service = AdmissionService()
    
    # Should acquire successfully
    await service.acquire()
    
    # Release it
    service.release()
    assert service.global_semaphore._value == settings.global_agent_concurrency

@pytest.mark.asyncio
async def test_admission_service_rejects_when_full():
    # Force limit to 1 for testing
    settings.global_agent_concurrency = 1
    service = AdmissionService()
    service.global_semaphore = asyncio.Semaphore(1)
    
    # First acquire should succeed
    await service.acquire()
    
    # Second should fail with 503
    with pytest.raises(HTTPException) as exc:
        await service.acquire(timeout=0.1)
    
    assert exc.value.status_code == 503
