from typing import Optional

from pydantic import BaseModel


class GatewayRequestContext(BaseModel):
    """
    Internal domain model representing the context of an incoming request 
    after it passes through admission and authentication, but before routing.
    """
    request_id: str
    tenant_id: str
    auth_scope: str
    is_priority: bool = False
    rate_limit_bucket: Optional[str] = None
