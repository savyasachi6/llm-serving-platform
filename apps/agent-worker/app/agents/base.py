from abc import ABC, abstractmethod
from typing import Any

from app.orchestration.task_graph import AgentResult, AgentTask


class BaseAgent(ABC):
    """
    Base class for all agents executed by the AgentWorker.
    """

    def __init__(self, name: str, system_prompt: str = ""):
        self.name = name
        self.system_prompt = system_prompt

    @abstractmethod
    async def execute(self, task: AgentTask, context: dict[str, Any]) -> AgentResult:
        """
        Executes the agent's core logic for a specific task.
        """
        pass
