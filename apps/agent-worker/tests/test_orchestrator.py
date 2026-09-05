from unittest.mock import AsyncMock

import pytest
from app.agents.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_successful_flow():
    orchestrator = Orchestrator()
    orchestrator.triage.execute = AsyncMock(return_value={"classification": "Billing"})
    orchestrator.redact.execute = AsyncMock(
        return_value={"redacted_text": "I was charged twice on [CARD-REDACTED]."}
    )
    orchestrator.respond.execute = AsyncMock(
        return_value={
            "final_reply": "We apologize for the duplicate charge. A refund is being processed."
        }
    )

    ticket = "I was charged twice on card 1234-5678-9012-3456."
    result = await orchestrator.process_ticket(ticket)

    assert result["original_ticket"] == ticket
    assert result["classification"] == "Billing"
    assert result["redacted_ticket"] == "I was charged twice on [CARD-REDACTED]."
    assert "refund is being processed" in result["final_reply"]


@pytest.mark.asyncio
async def test_orchestrator_empty_ticket_raises_error():
    orchestrator = Orchestrator()
    with pytest.raises(ValueError, match="Ticket text cannot be empty"):
        await orchestrator.process_ticket("")

    with pytest.raises(ValueError, match="Ticket text cannot be empty"):
        await orchestrator.process_ticket("   \n\t  ")


@pytest.mark.asyncio
async def test_orchestrator_halts_on_redaction_failure():
    """Security verification: If RedactAgent fails or returns empty text, pipeline MUST halt to prevent PII leakage."""
    orchestrator = Orchestrator()
    orchestrator.triage.execute = AsyncMock(return_value={"classification": "Technical"})
    orchestrator.redact.execute = AsyncMock(
        return_value={"redacted_text": ""}
    )  # Malformed/empty redaction

    with pytest.raises(RuntimeError, match="Security Violation: RedactAgent failed"):
        await orchestrator.process_ticket("My password is supersecret123.")


@pytest.mark.asyncio
async def test_orchestrator_upstream_agent_exception():
    orchestrator = Orchestrator()
    orchestrator.triage.execute = AsyncMock(side_effect=Exception("Gateway connection refused"))
    orchestrator.redact.execute = AsyncMock(return_value={"redacted_text": "sanitized"})

    with pytest.raises(RuntimeError, match="Pipeline halted: upstream agent failed"):
        await orchestrator.process_ticket("System crashed with error 500.")
