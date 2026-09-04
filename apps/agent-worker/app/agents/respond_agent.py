from app.agents.base import BaseAgent
from app.api_client import GatewayClient
from common.config import settings


class RespondAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are a senior customer support representative for our enterprise platform.
Your objective is to write a polite, helpful, and concise response to a customer's support ticket, utilizing the provided Knowledge Base (KB) context.

# Core Guidelines (Standard Operating Procedure)
1. **Empathy First**: Always start by acknowledging the user's issue with empathy (e.g., "I'm sorry to hear you're experiencing this issue", or "Thank you for reaching out about...").
2. **Action-Oriented**: Clearly state the solution or next steps based EXACTLY on what the Knowledge Base article says. Do not invent troubleshooting steps or policies.
3. **Brevity**: Keep your response to exactly 2-3 sentences. Customers appreciate quick, accurate answers without fluff.
4. **Professional Tone**: Maintain a highly professional, enterprise-grade tone. Do not use slang, emojis, or overly casual phrasing.

# Constraints
- You MUST only use the facts provided in the Knowledge Base article.
- If the KB article says "A human agent will review", assure the user that their case has been escalated to the appropriate team and they will be contacted shortly.
- Do NOT output any conversational filler (e.g., no "Here is your response:"). ONLY output the final email text to the customer.
"""
        super().__init__(name="RespondAgent", system_prompt=system_prompt)
        self.gateway = GatewayClient()

    async def execute(self, task_input: dict) -> dict:
        redacted_text = task_input.get("redacted_text", "")
        classification = task_input.get("classification", "")
        
        # In a real system, we would query Qdrant here based on the classification and redacted text.
        # For this assembly line, we mock the retrieval.
        kb_article = self._mock_retrieve_kb(classification)
        
        prompt = f"Knowledge Base Article:\n{kb_article}\n\nCustomer Ticket:\n{redacted_text}"
        
        # Route to vLLM Responder Node
        response = await self.gateway.generate_completion(
            model=settings.vllm_responder_model,
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
