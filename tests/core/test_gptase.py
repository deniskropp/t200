
import pytest
from unittest.mock import AsyncMock, patch, ANY
from src.core.agents.gptase import GPTASeAgent
from src.shared.models import AgentTask

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
    }, source_id="GPTASe")

@pytest.mark.asyncio
async def test_gptase_executes_task_failure(mock_bus):
    # Mock LLM that raises exception
    mock_llm = AsyncMock()
    mock_llm.generate.side_effect = Exception("LLM Generation Failed")
    
    agent = GPTASeAgent(bus=mock_bus, llm=mock_llm)
    await agent.start()
    
    # Mock sleep to be fast
    with patch('asyncio.sleep', AsyncMock()):
        
        task = AgentTask(id="999", type="TEST", title="Impossible Task", payload={}, assigned_to="GPTASe")
        await agent._handle_task_envelope(type('Envelope', (), {'payload': task})())

    # Verify result failure
    mock_bus.publish.assert_any_call("workflow.task_result", {
        "task_id": "999",
        "status": "FAILED",
        "error": "LLM Generation Failed",
        "agent_id": "GPTASe"
    }, source_id="GPTASe")
