from typing import Dict, Any
from app.agents.base import BaseAgent
from app.orchestration.task_graph import AgentTask, AgentResult

class ResearchAgent(BaseAgent):
    """
    An agent specialized in searching and summarizing information.
    """
    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            system_prompt="You are a research agent. Synthesize information accurately."
        )
        
    async def execute(self, task: AgentTask, context: Dict[str, Any]) -> AgentResult:
        # In a real implementation, this would call the Gateway's chat_completions endpoint
        # with its tools and system prompt.
        return AgentResult(
            task_id=task.id,
            content=f"Research completed for: {task.prompt}"
        )
