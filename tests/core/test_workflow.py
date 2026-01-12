
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from uuid import uuid4

from src.core.workflow.state import WorkflowState, TransitionError, validate_transition
from src.core.workflow.engine import WorkflowEngine
from src.core.workflow.guards import check_guards
from src.core.db.models import Goal

# Test validate_transition pure function
def test_validate_transition_valid():
    assert validate_transition(WorkflowState.INITIALIZATION, WorkflowState.TASK_DECOMPOSITION) is True

def test_validate_transition_invalid():
    with pytest.raises(TransitionError):
        validate_transition(WorkflowState.INITIALIZATION, WorkflowState.EXECUTION_MONITORING)

# Mocking the dependencies for WorkflowEngine
@pytest.fixture
def mock_bus():
    return AsyncMock()

@pytest.fixture
def mock_session():
    session = AsyncMock()
    # Mocking basic session behavior: add/commit are checking interaction only.
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    # Configure get to return None by default, specific tests override it
    session.get = AsyncMock(return_value=None)
    return session

@pytest.fixture
def mock_session_factory(mock_session):
    # Determine if we need to mock the context manager properly
    # session_factory() -> returns session context manager
    # async with session_factory() as session: ...
    
    # We need a MagicMock that returns an async context manager
    factory = MagicMock()
    # The return value of calling the factory is the context manager
    context_manager = MagicMock()
    context_manager.__aenter__.return_value = mock_session
    context_manager.__aexit__.return_value = None
    factory.return_value = context_manager
    
    return factory

@pytest.mark.asyncio
async def test_workflow_engine_initialize_goal(mock_bus, mock_session_factory, mock_session):
    engine = WorkflowEngine(bus=mock_bus, session_factory=mock_session_factory)
    
    goal_id = await engine.initialize_goal(title="Test Goal", description="Test Desc")
    
    assert mock_session.add.called
    assert mock_session.commit.called
    mock_bus.publish.assert_called_with("workflow.goal_started", ANY)

@pytest.mark.asyncio
async def test_workflow_engine_transition_valid(mock_bus, mock_session_factory, mock_session):
    engine = WorkflowEngine(bus=mock_bus, session_factory=mock_session_factory)
    
    # Setup a mock goal in INITIALIZATION state
    goal_id = uuid4()
    mock_goal = Goal(id=goal_id, title="Test", description="Desc", status=WorkflowState.INITIALIZATION.value)
    mock_session.get.return_value = mock_goal

    # Attempt transition to TASK_DECOMPOSITION
    success = await engine.transition_phase(goal_id, WorkflowState.TASK_DECOMPOSITION)
    
    assert success is True
    assert mock_goal.status == WorkflowState.TASK_DECOMPOSITION.value
    assert mock_session.commit.called
    mock_bus.publish.assert_called_with("workflow.state_change", {
        "goal_id": str(goal_id),
        "previous_state": WorkflowState.INITIALIZATION.value,
        "new_state": WorkflowState.TASK_DECOMPOSITION.value,
        "timestamp": ANY
    })

@pytest.mark.asyncio
async def test_workflow_engine_transition_invalid_transition(mock_bus, mock_session_factory, mock_session):
    engine = WorkflowEngine(bus=mock_bus, session_factory=mock_session_factory)
    
    # Setup a mock goal in INITIALIZATION state
    goal_id = uuid4()
    mock_goal = Goal(id=goal_id, title="Test", description="Desc", status=WorkflowState.INITIALIZATION.value)
    mock_session.get.return_value = mock_goal

    # Attempt transition directly to EXECUTION (Invalid)
    # This checks validate_transition logic inside engine
    with pytest.raises(TransitionError):
        await engine.transition_phase(goal_id, WorkflowState.EXECUTION_MONITORING)

@pytest.mark.asyncio
async def test_workflow_engine_transition_guard_failure(mock_bus, mock_session_factory, mock_session):
    engine = WorkflowEngine(bus=mock_bus, session_factory=mock_session_factory)
    
    # Setup a mock goal with MISSING TITLE/DESC to trigger guard failure
    goal_id = uuid4()
    mock_goal = Goal(id=goal_id, title="", description="", status=WorkflowState.INITIALIZATION.value)
    mock_session.get.return_value = mock_goal

    # Attempt transition (Should fail due to guard_goal_defined)
    with pytest.raises(TransitionError) as excinfo:
        await engine.transition_phase(goal_id, WorkflowState.TASK_DECOMPOSITION)
    
    assert "Goal title and description are required" in str(excinfo.value)

