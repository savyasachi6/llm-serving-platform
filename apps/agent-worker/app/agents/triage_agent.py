from app.agents.base import BaseAgent
from app.api_client import GatewayClient
from common.config import settings

class TriageAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="TriageAgent", description="Classifies customer support tickets")
        self.gateway = GatewayClient()
        self.system_prompt = "You are a customer support triage agent. Classify this ticket as 'Billing', 'Technical', or 'General'. Output exactly one word."

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
