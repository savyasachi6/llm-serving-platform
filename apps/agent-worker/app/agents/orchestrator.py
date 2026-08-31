import asyncio
from app.agents.triage_agent import TriageAgent
from app.agents.redact_agent import RedactAgent
from app.agents.respond_agent import RespondAgent

class Orchestrator:
    def __init__(self):
        self.triage = TriageAgent()
        self.redact = RedactAgent()
        self.respond = RespondAgent()
        
    async def process_ticket(self, ticket_text: str) -> dict:
        """
        The Micro-Agent Assembly Line.
        Steps run concurrently where possible, or sequentially if they depend on each other.
        """
        # Step 1: Triage (Classification)
        triage_task = asyncio.create_task(self.triage.execute({"ticket_text": ticket_text}))
        
        # Step 2: Redact PII
        redact_task = asyncio.create_task(self.redact.execute({"ticket_text": ticket_text}))
        
        # Wait for both triage and redaction to finish
        triage_result, redact_result = await asyncio.gather(triage_task, redact_task)
        
        # Step 3: Respond (Requires both classification and redacted text)
        respond_result = await self.respond.execute({
            "classification": triage_result["classification"],
            "redacted_text": redact_result["redacted_text"]
        })
        
        return {
            "original_ticket": ticket_text,
            "classification": triage_result["classification"],
            "redacted_ticket": redact_result["redacted_text"],
            "final_reply": respond_result["final_reply"]
        }
