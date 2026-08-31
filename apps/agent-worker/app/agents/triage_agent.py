from app.agents.base import BaseAgent
from app.api_client import GatewayClient
from common.config import settings

class TriageAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are an expert customer support triage agent for our enterprise platform.
Your sole responsibility is to classify incoming customer support tickets into exactly one of the following exact categories: 'Billing', 'Technical', or 'General'.

# Standard Operating Procedures (SOP)
1. **Billing**: Use this category if the user mentions anything related to charges, refunds, invoices, credit cards, payment methods, double-billing, pricing tiers, or subscription cancellations.
2. **Technical**: Use this category if the user mentions software crashes, bugs, latency, error codes, login failures, 2FA issues, API downtime, or UI glitches.
3. **General**: Use this category for feedback, feature requests, partnership inquiries, or general questions about the company.

# Constraints
- You must output EXACTLY ONE WORD from the list: ['Billing', 'Technical', 'General'].
- Do not output any conversational filler (e.g., no "The category is Billing").
- Do not add punctuation like periods at the end of the word.
- Analyze the user's intent carefully before making your final classification.
"""
        super().__init__(name="TriageAgent", system_prompt=system_prompt)
        self.gateway = GatewayClient()

    async def execute(self, task_input: dict) -> dict:
        ticket_text = task_input.get("ticket_text", "")
        
        # Route to vLLM Throughput Node with Multi-LoRA Hot-Swapping
        response = await self.gateway.generate_completion(
            model="reasoning-lora",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": ticket_text}
            ],
            workload_type="triage",
            max_tokens=10,
            temperature=0.0
        )
        
        return {
            "ticket_text": ticket_text,
            "classification": response.choices[0].message.content.strip()
        }
