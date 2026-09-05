from app.api.routes import chat_completions, health, metrics
from app.lifespan import lifespan
from app.shared.ids import generate_request_id, generate_trace_id
from common.telemetry import request_id_var, trace_id_var
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Agentic LLM Serving Gateway", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    # Extract or generate correlation IDs
    req_id = request.headers.get("X-Request-ID", generate_request_id())
    trace_id = request.headers.get("X-Trace-ID", generate_trace_id())

    request_id_var.set(req_id)
    trace_id_var.set(trace_id)

    response = await call_next(request)

    response.headers["X-Request-ID"] = req_id
    response.headers["X-Trace-ID"] = trace_id

    return response


app.include_router(health.router, tags=["health"])
app.include_router(metrics.router, tags=["metrics"])
app.include_router(chat_completions.router, tags=["chat"])

if __name__ == "__main__":
    import uvicorn
    from common.config import settings

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.gateway_port, reload=True)
