from typing import Annotated
from fastapi import Depends
from app.application.admission_service import AdmissionService
from app.application.routing_service import RoutingService

# Global instances
_admission_service = AdmissionService()
_routing_service = RoutingService(use_mock=True) # default to mock for testing phases

def get_admission_service() -> AdmissionService:
    return _admission_service

def get_routing_service() -> RoutingService:
    return _routing_service

AdmissionDependency = Annotated[AdmissionService, Depends(get_admission_service)]
RoutingDependency = Annotated[RoutingService, Depends(get_routing_service)]
