import pytest
import asyncio
from app.orchestration.task_graph import AgentExecutor, AgentTask, CancellationToken, AgentResult

@pytest.mark.asyncio
async def test_agent_executor_cancellation():
    executor = AgentExecutor(concurrency_limit=1)
    token = CancellationToken()
    task = AgentTask(id="1", name="test", prompt="hello")
    
    token.cancel()
    
    async def mock_runner(t: AgentTask):
        return AgentResult(task_id=t.id, content="done")
        
    result = await executor.execute_task(task, token, mock_runner)
    assert result.error is not None
    assert "Cancelled" in result.error
    assert task.status == "cancelled"

@pytest.mark.asyncio
async def test_agent_executor_success():
    executor = AgentExecutor(concurrency_limit=1)
    token = CancellationToken()
    task = AgentTask(id="1", name="test", prompt="hello")
    
    async def mock_runner(t: AgentTask):
        return AgentResult(task_id=t.id, content="done")
        
    result = await executor.execute_task(task, token, mock_runner)
    assert result.error is None
    assert result.content == "done"
    assert task.status == "completed"
