
import pytest
from unittest.mock import AsyncMock, patch, ANY
from src.core.agents.gptase import GPTASeAgent
from src.ocs.shared.models import AgentTask

@pytest.fixture
def mock_bus():
    return AsyncMock()

@pytest.mark.asyncio
async def test_gptase_executes_task_success(mock_bus):
    agent = GPTASeAgent(bus=mock_bus)
    await agent.start()
    
    # Mock sleep and random to ensure success path
    with patch('asyncio.sleep', AsyncMock()), \
         patch('random.random', return_value=0.5), \
         patch('random.uniform', return_value=0.1):
        
        task = AgentTask(id="123", type="TEST", title="Execute Order 66", payload={}, assigned_to="GPTASe")
        await agent._handle_task_envelope(type('Envelope', (), {'payload': task})())

    # Verify logs
    mock_bus.publish.assert_any_call("agent.log", {
        "agent_id": "GPTASe",
        "level": "SUCCESS",
        "message": ANY
    })
    
    # Verify result
    mock_bus.publish.assert_any_call("workflow.task_result", {
        "task_id": "123",
        "status": "COMPLETED",
        "result": ANY,
        "agent_id": "GPTASe"
    })

@pytest.mark.asyncio
async def test_gptase_executes_task_failure(mock_bus):
    agent = GPTASeAgent(bus=mock_bus)
    await agent.start()
    
    # Mock random to trigger failure (< 0.1)
    with patch('asyncio.sleep', AsyncMock()), \
         patch('random.random', return_value=0.05):
        
        task = AgentTask(id="999", type="TEST", title="Impossible Task", payload={}, assigned_to="GPTASe")
        await agent._handle_task_envelope(type('Envelope', (), {'payload': task})())

    # Verify result failure (BaseAgent handles failure, publishes to workflow.task_result now)
    mock_bus.publish.assert_any_call("workflow.task_result", {
        "task_id": "999",
        "status": "FAILED",
        "error": "Random execution glitch in quantum matrix.",
        "agent_id": "GPTASe"
    }, source_id="GPTASe")
