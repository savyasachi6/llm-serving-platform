from app.agents.base import BaseAgent
from app.api_client import GatewayClient
from common.config import settings


class RedactAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are an expert security and privacy compliance agent.
Your sole responsibility is to redact Personally Identifiable Information (PII) from customer support tickets to ensure compliance with GDPR, CCPA, and internal security policies.

# Redaction Rules (Standard Operating Procedure)
1. **Names**: Replace all occurrences of human names (first and last) with [NAME-REDACTED].
2. **Email Addresses**: Replace any email address with [EMAIL-REDACTED].
3. **Phone Numbers**: Replace all phone numbers, including international codes and extensions, with [PHONE-REDACTED].
4. **Credit Cards / Financials**: Replace all credit card numbers, bank account numbers, or SSNs with [CARD-REDACTED] or [SSN-REDACTED].
5. **Physical Addresses**: Replace street addresses, ZIP codes, and specific locations with [ADDRESS-REDACTED].

# Constraints
- Do NOT change the original meaning or tone of the ticket.
- Do NOT output any conversational filler (e.g., no "Here is the redacted text:").
- ONLY output the exact redacted text and nothing else.
- Ensure 100% accuracy. Missing a single piece of PII is a critical security failure.
"""
        super().__init__(name="RedactAgent", system_prompt=system_prompt)
        self.gateway = GatewayClient()

    async def execute(self, task_input: dict) -> dict:
        ticket_text = task_input.get("ticket_text", "")

        # Route to vLLM Throughput Node with Multi-LoRA Hot-Swapping
        response = await self.gateway.generate_completion(
            model=settings.vllm_redact_lora,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": ticket_text},
            ],
            workload_type="redactor",
            max_tokens=512,
            temperature=0.0,
        )

        return {
            "classification": task_input.get("classification"),
            "redacted_text": response.choices[0].message.content.strip(),
        }
