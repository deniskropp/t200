
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from uuid import uuid4, UUID
from src.core.agents.lyra import LyraAgent
from src.core.bus.bus import MessageEnvelope
from src.core.db.models import Goal

@pytest.fixture
def mock_bus():
    return AsyncMock()

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.get = AsyncMock()
    return session

@pytest.fixture
def mock_session_factory(mock_session):
    return MagicMock(return_value=MagicMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))

@pytest.mark.asyncio
async def test_lyra_reacts_to_decomposition_request(mock_bus, mock_session_factory, mock_session):
    lyra = LyraAgent(bus=mock_bus, session_factory=mock_session_factory)
    await lyra.start()
    
    # Check subscription
    mock_bus.subscribe.assert_any_call("agent.lyra.decompose", lyra.on_decompose_request)

    # Setup mock goal
    goal_id = str(uuid4())
    mock_goal = Goal(id=UUID(goal_id), title="Test Goal", description="Desc")
    mock_session.get.return_value = mock_goal

    # Simulate Request
    payload = {"goal_id": goal_id, "title": "Test Goal"}
    envelope = MessageEnvelope(topic="agent.lyra.decompose", payload=payload, source_id="director")
    
    with patch('asyncio.sleep', AsyncMock()): # skip sleep
        await lyra.on_decompose_request(envelope)

    # Verification
    # 1. Session should have retrieved goal
    mock_session.get.assert_called_with(Goal, UUID(goal_id))
    
    # 2. Tasks should be added
    assert mock_session.add.call_count == 3
    assert mock_session.commit.called
    
    # 3. Success log
    mock_bus.publish.assert_any_call("agent.log", {
        "agent_id": "Lyra",
        "level": "SUCCESS",
        "message": "Decomposed goal into 3 tasks."
    })
    
    # 4. Tasks generated event
    mock_bus.publish.assert_any_call("workflow.tasks_generated", {
        "goal_id": goal_id,
        "task_count": 3
    })
