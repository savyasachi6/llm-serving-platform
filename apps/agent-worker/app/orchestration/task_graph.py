import asyncio
from typing import Awaitable, Callable, Dict, List

from pydantic import BaseModel


class TaskStatus:
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AgentTask(BaseModel):
    id: str
    name: str
    priority: int = 0
    prompt: str
    dependencies: List[str] = []
    status: str = TaskStatus.PENDING

class AgentResult(BaseModel):
    task_id: str
    content: str | None = None
    error: str | None = None
    
class CancellationToken:
    def __init__(self):
        self._is_cancelled = False
        self._event = asyncio.Event()
        
    def cancel(self):
        self._is_cancelled = True
        self._event.set()
        
    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled
        
    async def wait(self):
        await self._event.wait()

class TaskGraph:
    def __init__(self):
        self.tasks: Dict[str, AgentTask] = {}
        
    def add_task(self, task: AgentTask):
        self.tasks[task.id] = task

class AgentExecutor:
    def __init__(self, concurrency_limit: int = 10):
        self.semaphore = asyncio.Semaphore(concurrency_limit)
        
    async def execute_task(self, task: AgentTask, token: CancellationToken, runner: Callable[[AgentTask], Awaitable[AgentResult]]) -> AgentResult:
        if token.is_cancelled:
            task.status = TaskStatus.CANCELLED
            return AgentResult(task_id=task.id, error="Cancelled before execution")
            
        async with self.semaphore:
            if token.is_cancelled:
                task.status = TaskStatus.CANCELLED
                return AgentResult(task_id=task.id, error="Cancelled during semaphore wait")
                
            task.status = TaskStatus.RUNNING
            try:
                # Actual execution delegated to runner (which might make an HTTP call to gateway)
                result = await runner(task)
                task.status = TaskStatus.COMPLETED
                return result
            except Exception as e:
                task.status = TaskStatus.FAILED
                return AgentResult(task_id=task.id, error=str(e))
