from typing import Annotated, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.core.workflow.engine import WorkflowEngine
from src.core.workflow.state import WorkflowState, TransitionError
from src.api.deps import get_engine

router = APIRouter()

class CreateGoalRequest(BaseModel):
    title: str
    description: str

class TransitionRequest(BaseModel):
    target_state: WorkflowState

@router.post("/goals", status_code=status.HTTP_201_CREATED)
async def create_goal(
    request: CreateGoalRequest,
    engine: Annotated[WorkflowEngine, Depends(get_engine)]
) -> dict[str, str]:
    """Create a new High-Level Goal (Starts N1)."""
    goal_id = await engine.initialize_goal(request.title, request.description)
    return {"id": str(goal_id), "status": "created"}

@router.post("/goals/{goal_id}/advance")
async def advance_phase(
    goal_id: UUID,
    request: TransitionRequest,
    engine: Annotated[WorkflowEngine, Depends(get_engine)]
) -> dict[str, Any]:
    """Advance a goal to the next phase."""
    try:
        success = await engine.transition_phase(goal_id, request.target_state)
        return {"goal_id": str(goal_id), "new_state": request.target_state, "accepted": success}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/goals/{goal_id}/tasks")
async def get_goal_tasks(
    goal_id: UUID,
    engine: Annotated[WorkflowEngine, Depends(get_engine)]
) -> Any:
    """Retrieve tasks for a specific goal."""
    from sqlalchemy import select
    from src.core.db.models import Task
    
    # We use engine's session factory directly here for simplicity
    async with engine.session_factory() as session:
        result = await session.execute(select(Task).where(Task.goal_id == goal_id))
        tasks = result.scalars().all()
        return tasks
