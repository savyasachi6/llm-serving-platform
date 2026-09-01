
# NOTE on imports:
# The monorepo uses a uv workspace (see root pyproject.toml). When running via
# `uv run`, the shared packages (common, contracts, prompt-engine, retrieval)
# are automatically available on Python's path because they are listed as
# workspace members. The root pyproject.toml also configures pytest pythonpath
# so tests can resolve these imports. No sys.path hacks are needed.
from app.agents.orchestrator import Orchestrator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Agent Worker Pipeline API")

# Allow CORS for the local React playground
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TicketRequest(BaseModel):
    ticket_text: str

orchestrator = Orchestrator()

@app.post("/api/process_ticket")
async def process_ticket(req: TicketRequest):
    """
    Executes the multi-agent pipeline: Triage & Redact (parallel) -> Synthesize Response.
    """
    try:
        result = await orchestrator.process_ticket(req.ticket_text)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=8001, reload=True)
