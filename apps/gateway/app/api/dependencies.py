# Force Docker Cache Bust 3
from typing import Annotated

from app.application.admission_service import AdmissionService
from app.application.routing_service import RoutingService
from fastapi import Depends

from common.config import settings

# Global instances
_admission_service = AdmissionService()
_routing_service = RoutingService(use_mock=settings.use_mock)

def get_admission_service() -> AdmissionService:
    return _admission_service

def get_routing_service() -> RoutingService:
    return _routing_service

AdmissionDependency = Annotated[AdmissionService, Depends(get_admission_service)]
RoutingDependency = Annotated[RoutingService, Depends(get_routing_service)]
