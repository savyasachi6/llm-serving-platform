import structlog
from contextvars import ContextVar

# Context variables for structured logging
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
tenant_scope_var: ContextVar[str] = ContextVar("tenant_scope", default="")
workload_type_var: ContextVar[str] = ContextVar("workload_type", default="")

def add_context_vars(logger, method_name, event_dict):
    """Add context variables to log event."""
    req_id = request_id_var.get()
    if req_id:
        event_dict["request_id"] = req_id
        
    trace_id = trace_id_var.get()
    if trace_id:
        event_dict["trace_id"] = trace_id
        
    tenant = tenant_scope_var.get()
    if tenant:
        event_dict["tenant_scope"] = tenant
        
    workload = workload_type_var.get()
    if workload:
        event_dict["workload_type"] = workload
        
    return event_dict

def setup_logging():
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            add_context_vars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )

def get_logger(name: str):
    return structlog.get_logger(name)
