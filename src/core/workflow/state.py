from enum import Enum, auto
from typing import Dict, List, Set

from pydantic import BaseModel

class WorkflowState(str, Enum):
    INITIALIZATION = "N1_INITIALIZATION"
    TASK_DECOMPOSITION = "N2_TASK_DECOMPOSITION"
    DESIGN_IMPLEMENTATION = "N3_DESIGN_IMPLEMENTATION"
    EXECUTION_MONITORING = "N4_EXECUTION_MONITORING"
    META_COMMUNICATION = "N5_META_COMMUNICATION"
    KICKLANG_INTEGRATION = "N6_KICKLANG_INTEGRATION"
    
    # Meta States
    SUSPENDED = "SUSPENDED"
    COMPLETED = "COMPLETED"

class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

class WorkflowTransition(BaseModel):
    from_state: WorkflowState
    to_state: WorkflowState
    required_conditions: List[str] = []

# Define allowed transitions (Adjacency List)
TRANSITION_MAP: Dict[WorkflowState, Set[WorkflowState]] = {
    WorkflowState.INITIALIZATION: {WorkflowState.TASK_DECOMPOSITION},
    WorkflowState.TASK_DECOMPOSITION: {WorkflowState.DESIGN_IMPLEMENTATION},
    WorkflowState.DESIGN_IMPLEMENTATION: {WorkflowState.EXECUTION_MONITORING},
    WorkflowState.EXECUTION_MONITORING: {
        WorkflowState.META_COMMUNICATION, 
        WorkflowState.KICKLANG_INTEGRATION,
        WorkflowState.EXECUTION_MONITORING, # Loop N4->N4
        WorkflowState.SUSPENDED
    },
    WorkflowState.META_COMMUNICATION: {WorkflowState.EXECUTION_MONITORING, WorkflowState.INITIALIZATION},
    WorkflowState.KICKLANG_INTEGRATION: {WorkflowState.COMPLETED},
    WorkflowState.SUSPENDED: {WorkflowState.INITIALIZATION, WorkflowState.EXECUTION_MONITORING}, # Manual recovery
}

def validate_transition(current: WorkflowState, target: WorkflowState) -> bool:
    if target not in TRANSITION_MAP.get(current, set()):
        raise TransitionError(f"Invalid transition: {current} -> {target}")
    return True
