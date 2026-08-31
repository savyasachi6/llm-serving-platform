from app.agents.base import BaseAgent
from app.api_client import GatewayClient

class RespondAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="RespondAgent", description="Writes a reply using provided KB context")
        self.gateway = GatewayClient()
        self.system_prompt = "You are a customer support agent. Use the provided Knowledge Base article to write a polite, helpful 2-sentence reply to the customer's ticket."

    async def execute(self, task_input: dict) -> dict:
        redacted_text = task_input.get("redacted_text", "")
        classification = task_input.get("classification", "")
        
        # In a real system, we would query Qdrant here based on the classification and redacted text.
        # For this assembly line, we mock the retrieval.
        kb_article = self._mock_retrieve_kb(classification)
        
        prompt = f"Knowledge Base Article:\n{kb_article}\n\nCustomer Ticket:\n{redacted_text}"
        
        # Route to vLLM Precision Node (Gemma-2-2B-it)
        response = await self.gateway.generate_completion(
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            workload_type="responder",
            max_tokens=150,
            temperature=0.7
        )
        
        return {
            "classification": classification,
            "final_reply": response.choices[0].message.content.strip()
        }

    def _mock_retrieve_kb(self, classification: str) -> str:
        if classification.lower() == "billing":
            return "To update a credit card, go to Settings > Billing and click 'Update Payment Method'. Refunds take 3-5 business days."
        elif classification.lower() == "technical":
            return "If the app crashes on startup, please clear your browser cache and disable ad-blockers. If the issue persists, reinstall the app."
        else:
            return "Thank you for reaching out. A human agent will review your request shortly."
