"""
Interactive script to run and test the Micro-Agent Assembly Line.
Demonstrates:
  1. Triage Agent (Classification with LoRA)
  2. Redaction Agent (PII Masking with LoRA)
  3. Respond Agent (Gemma-2B Synthesis)
"""
import asyncio
import os
import sys

# Ensure project modules can be found
sys.path.insert(0, os.path.abspath("apps/agent-worker"))
sys.path.insert(0, os.path.abspath("apps/gateway"))
sys.path.insert(0, os.path.abspath("packages/common/src"))
sys.path.insert(0, os.path.abspath("packages/contracts/src"))
sys.path.insert(0, os.path.abspath("packages/prompt-engine/src"))
sys.path.insert(0, os.path.abspath("packages/retrieval/src"))

from app.agents.orchestrator import Orchestrator

async def main():
    print("==================================================")
    print("[*] Micro-Agent Assembly Line - Pipeline Test")
    print("==================================================")
    
    sample_ticket = (
        "Hi, my name is Jane Doe (SSN: 000-12-3456, email: jane.doe@example.com). "
        "I was charged $120.00 twice on invoice #98765 on my credit card 4532-1234-5678-9012. "
        "Please issue a refund immediately!"
    )
    
    print(f"\n[Incoming Customer Ticket]:\n{sample_ticket}\n")
    print("Running Assembly Line (Triage + Redact in parallel -> Response synthesis)...")
    
    orchestrator = Orchestrator()
    result = await orchestrator.process_ticket(sample_ticket)
    
    print("\n--- Pipeline Execution Results ---")
    print(f"[1] Classification (Triage Agent) : {result['classification']}")
    print(f"[2] Redacted Ticket (Redact Agent): {result['redacted_ticket']}")
    print(f"[3] Final Reply (Respond Agent)   : {result['final_reply']}")
    print("\n==================================================")
    print("[SUCCESS] Pipeline completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
