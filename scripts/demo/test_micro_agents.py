"""Interactive demonstration and test script for the Micro-Agent Pipeline.

Demonstrates the sequential customer support workflow:
  1. Triage Agent: Classifies ticket intent (using reasoning-lora).
  2. Redact Agent: Scrubs sensitive PII like SSNs and credit cards (using reflection-lora).
  3. Respond Agent: Synthesizes final personalized resolution response.

Usage:
    python scripts/demo/test_micro_agents.py
"""

import asyncio
import pathlib
import sys

# Ensure project workspace modules are resolvable
repo_root = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root / "apps" / "agent-worker"))
sys.path.insert(0, str(repo_root / "apps" / "gateway"))
sys.path.insert(0, str(repo_root / "packages" / "common" / "src"))
sys.path.insert(0, str(repo_root / "packages" / "contracts" / "src"))
sys.path.insert(0, str(repo_root / "packages" / "prompt-engine" / "src"))
sys.path.insert(0, str(repo_root / "packages" / "retrieval" / "src"))

from app.agents.orchestrator import Orchestrator  # noqa: E402


async def main():
    print("=" * 60)
    print("🤖 Micro-Agent Assembly Line - Pipeline Demonstration")
    print("=" * 60)

    sample_ticket = (
        "Hi, my name is Jane Doe (SSN: 000-12-3456, email: jane.doe@example.com). "
        "I was charged $120.00 twice on invoice #98765 on my credit card 4532-1234-5678-9012. "
        "Please issue a refund immediately!"
    )

    print(f"\n[Incoming Customer Ticket]:\n{sample_ticket}\n")
    print("Running Pipeline: (Triage + Redact in parallel -> Response synthesis)...")

    orchestrator = Orchestrator()
    result = await orchestrator.process_ticket(sample_ticket)

    print("\n--- Pipeline Execution Results ---")
    print(f"[1] Classification (Triage Agent) : {result['classification']}")
    print(f"[2] Redacted Ticket (Redact Agent): {result['redacted_ticket']}")
    print(f"[3] Final Reply (Respond Agent)   : {result['final_reply']}")
    print("=" * 60)
    print("[SUCCESS] Pipeline completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
