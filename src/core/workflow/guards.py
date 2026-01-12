from typing import Any, Awaitable, Callable, Dict, List, Tuple
from src.core.db.models import Goal
from src.core.workflow.state import WorkflowState, TransitionError

# Guards are async functions that take a Goal and return True if valid, or raise/return False.
GuardFunction = Callable[[Goal], Awaitable[bool]]

async def guard_goal_defined(goal: Goal) -> bool:
    """Ensure Goal has basic metadata."""
    if not goal.title or not goal.description:
        raise TransitionError("Goal title and description are required.")
    return True

async def guard_task_decomposition_done(goal: Goal) -> bool:
    """Ensure Tasks have been generated (placeholder)."""
    # In real imp, we query DB for tasks associated with goal
    # For now, we assume if we are moving, we might check something. 
    # But strictly, N2 -> N3 requires "Tasks & Prompts Ready".
    # We can check specific artifacts or task counts.
    return True

# Map (From, To) -> List[Guard]
TRANSITION_GUARDS: Dict[Tuple[WorkflowState, WorkflowState], List[GuardFunction]] = {
    (WorkflowState.INITIALIZATION, WorkflowState.TASK_DECOMPOSITION): [guard_goal_defined],
    # Add more as we implement features
}

async def check_guards(goal: Goal, target_state: WorkflowState) -> None:
    """Checks all guards for the transition from goal.status to target_state."""
    current_state = WorkflowState(goal.status)
    guards = TRANSITION_GUARDS.get((current_state, target_state), [])
    
    for guard in guards:
        try:
            valid = await guard(goal)
            if not valid:
                 raise TransitionError(f"Guard '{guard.__name__}' failed.")
        except TransitionError:
            raise
        except Exception as e:
            raise TransitionError(f"Guard '{guard.__name__}' raised error: {e}")
