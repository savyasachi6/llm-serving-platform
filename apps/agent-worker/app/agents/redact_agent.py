from app.agents.base import BaseAgent
from app.api_client import GatewayClient

class RedactAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RedactAgent", description="Removes PII from tickets")
        self.gateway = GatewayClient()
        self.system_prompt = "Rewrite this text replacing all names, emails, and phone numbers with [REDACTED]. Do not output anything else."

    async def execute(self, task_input: dict) -> dict:
        ticket_text = task_input.get("ticket_text", "")
        
        # Route to vLLM Throughput Node with Multi-LoRA Hot-Swapping
        response = await self.gateway.generate_completion(
            model="reflection-lora",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": ticket_text}
            ],
            workload_type="redactor",
            max_tokens=512,
            temperature=0.0
        )
        
        return {
            "classification": task_input.get("classification"),
            "redacted_text": response.choices[0].message.content.strip()
        }
