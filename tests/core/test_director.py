
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from uuid import uuid4, UUID
from src.core.agents.director import DirectorAgent
from src.core.workflow.state import WorkflowState
from src.core.bus.bus import MessageEnvelope

@pytest.fixture
def mock_bus():
    bus = AsyncMock()
    # Mock subscribe to store callback to simulate event later if needed, 
    # OR we can just call the callback directly in test.
    return bus

@pytest.fixture
def mock_engine():
    engine = MagicMock()
    # Transition phase is async
    engine.transition_phase = AsyncMock()
    # session_factory returns a context manager, so it's a normal function that returns an object
    # By default MagicMock will return a MagicMock, which is fine, but we customize it in test.
    return engine

@pytest.mark.asyncio
async def test_director_initialization(mock_bus, mock_engine):
    director = DirectorAgent(bus=mock_bus, engine=mock_engine)
    await director.start()
    
    # Check subscriptions
    mock_bus.subscribe.assert_any_call("workflow.goal_started", director.on_goal_started)
    mock_bus.subscribe.assert_any_call("workflow.state_change", director.on_state_change)

@pytest.mark.asyncio
async def test_director_reacts_to_new_goal(mock_bus, mock_engine):
    director = DirectorAgent(bus=mock_bus, engine=mock_engine)
    
    goal_id = str(uuid4())
    payload = {"goal_id": goal_id, "title": "Test Goal"}
    envelope = MessageEnvelope(topic="workflow.goal_started", payload=payload, source_id="test")
    
    # Mock sleep to run instantly
    with patch('asyncio.sleep', AsyncMock()):
        await director.on_goal_started(envelope)
    
    # Assert engine transition called
    mock_engine.transition_phase.assert_called_with(UUID(goal_id), WorkflowState.TASK_DECOMPOSITION)

@pytest.mark.asyncio
async def test_director_logs_and_delegates_on_state_change(mock_bus, mock_engine, caplog):
    director = DirectorAgent(bus=mock_bus, engine=mock_engine)
    
    # Mocking session for delegation logic
    mock_session = AsyncMock()
    mock_goal = MagicMock()
    mock_goal.title = "Delegated Goal"
    mock_goal.description = "Desc"
    mock_session.get.return_value = mock_goal
    
    # Correctly mock session_factory to return an async context manager
    # Calling engine.session_factory() returns the CM
    context_manager = MagicMock()
    context_manager.__aenter__.return_value = mock_session
    context_manager.__aexit__.return_value = None
    
    # configure the engine.session_factory Mock to return this CM
    mock_engine.session_factory.return_value = context_manager

    with caplog.at_level("INFO"):
        goal_id = str(uuid4())
        payload = {
            "goal_id": goal_id, 
            "new_state": WorkflowState.TASK_DECOMPOSITION.value,
            "previous_state": WorkflowState.INITIALIZATION.value
        }
        envelope = MessageEnvelope(topic="workflow.state_change", payload=payload, source_id="test")
        
        await director.on_state_change(envelope)
        
    assert "Director observed state change" in caplog.text
    assert "searching for Lyra" in caplog.text
    assert "Delegated goal" in caplog.text
    
    # Verify bus message
    mock_bus.publish.assert_any_call("agent.lyra.decompose", {
        "goal_id": goal_id,
        "title": "Delegated Goal",
        "description": "Desc"
    })
