# 🤖 Multi-Agent Pipeline Demonstration

This directory contains demonstration and live evaluation scripts for the platform's multi-agent customer support assembly line.

---

## 🏃 Running the Demo
```bash
# In USE_MOCK=True mode or with live inference backends running:
python scripts/demo/test_micro_agents.py
```

### What Happens:
1. An unredacted customer support ticket with sensitive PII (SSN, credit card, email) is fed into the pipeline.
2. The **Agent Orchestrator** dispatches the ticket to:
   - **TriageAgent** (classifies billing/support intent using `reasoning-lora`).
   - **RedactAgent** (anonymizes SSN and credit card tokens using `reflection-lora`).
3. Once both tasks complete, **RespondAgent** synthesizes a personalized resolution using the sanitized context.
