from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx
from common.telemetry import setup_logging

# Global HTTP client
http_client: httpx.AsyncClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    
    global http_client
    # Create lifespan-managed HTTP client with bounded connection pool
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    timeout = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=10.0)
    http_client = httpx.AsyncClient(limits=limits, timeout=timeout)
    
    yield
    
    # Shutdown
    if http_client:
        await http_client.aclose()

def get_http_client() -> httpx.AsyncClient:
    global http_client
    if http_client is None:
        raise RuntimeError("HTTP Client not initialized")
    return http_client
