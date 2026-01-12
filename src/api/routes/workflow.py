from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.core.workflow.engine import WorkflowEngine
from src.core.workflow.state import WorkflowState, TransitionError

router = APIRouter()

class GoalCreate(BaseModel):
    title: str
    description: str

class TransitionRequest(BaseModel):
    target_state: WorkflowState

@router.post("/goals", response_model=dict)
async def create_goal(data: GoalCreate):
    engine = WorkflowEngine()
    goal_id = await engine.initialize_goal(data.title, data.description)
    return {"goal_id": goal_id, "status": "created"}

@router.post("/goals/{goal_id}/transition")
async def transition_goal(goal_id: UUID, req: TransitionRequest):
    engine = WorkflowEngine()
    try:
        success = await engine.transition_phase(goal_id, req.target_state)
        return {"goal_id": goal_id, "new_state": req.target_state, "success": success}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
