import asyncio
import logging
from app.agents.triage_agent import TriageAgent
from app.agents.redact_agent import RedactAgent
from app.agents.respond_agent import RespondAgent

logger = logging.getLogger("agent-worker.orchestrator")

class Orchestrator:
    def __init__(self):
        self.triage = TriageAgent()
        self.redact = RedactAgent()
        self.respond = RespondAgent()
        
    async def process_ticket(self, ticket_text: str) -> dict:
        """
        The Micro-Agent Assembly Line.
        Steps run concurrently where possible, with strict failure isolation on PII redaction.
        """
        if not ticket_text or not ticket_text.strip():
            raise ValueError("Ticket text cannot be empty.")

        # Step 1 & 2: Concurrently trigger Triage (Classification) and Redaction (PII Masking)
        triage_task = asyncio.create_task(self.triage.execute({"ticket_text": ticket_text}))
        redact_task = asyncio.create_task(self.redact.execute({"ticket_text": ticket_text}))
        
        # Await both tasks; if either raises an exception, handle with strict safety boundaries
        try:
            triage_result, redact_result = await asyncio.gather(triage_task, redact_task)
        except Exception as exc:
            logger.error(f"Assembly line failure in preprocessing stages: {exc}")
            raise RuntimeError(f"Pipeline halted: upstream agent failed during processing ({exc})") from exc

        # Strict Failure Isolation & Security Check:
        # Redaction MUST succeed and produce non-empty text. If it fails or returns malformed data,
        # HALT immediately to prevent leaking raw PII to downstream response models.
        redacted_text = redact_result.get("redacted_text") if isinstance(redact_result, dict) else None
        if not redacted_text or not redacted_text.strip():
            logger.critical("PII Redaction failed or returned empty text. Halting pipeline to prevent data leakage.")
            raise RuntimeError("Security Violation: RedactAgent failed to produce sanitized text. Pipeline terminated.")

        classification = triage_result.get("classification", "General")

        # Step 3: Respond (Requires verified classification and sanitized redacted text)
        try:
            respond_result = await self.respond.execute({
                "classification": classification,
                "redacted_text": redacted_text
            })
        except Exception as exc:
            logger.error(f"RespondAgent failed during synthesis: {exc}")
            raise RuntimeError(f"Pipeline halted: Response synthesis failed ({exc})") from exc
        
        return {
            "original_ticket": ticket_text,
            "classification": classification,
            "redacted_ticket": redacted_text,
            "final_reply": respond_result.get("final_reply", "")
        }
