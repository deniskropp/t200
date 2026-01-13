from typing import Any, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, timezone

from src.core.workflow.state import WorkflowState, validate_transition
from src.core.db.session import AsyncSessionLocal
from src.core.db.models import Goal

if TYPE_CHECKING:
    from src.core.bus.bus import MessageBus

from src.core.workflow.guards import check_guards

class WorkflowEngine:
    def __init__(
        self, 
        bus: "MessageBus", 
        session_factory: Any = AsyncSessionLocal
    ) -> None:
        self.bus: "MessageBus" = bus
        self.session_factory = session_factory

    async def initialize_goal(self, title: str, description: str) -> UUID:
        """Starts a new orchestration cycle (N1)."""
        async with self.session_factory() as session:
            goal = Goal(
                title=title,
                description=description,
                status=WorkflowState.INITIALIZATION.value
            )
            session.add(goal)
            await session.commit()
            await session.refresh(goal)
            
            await self.bus.publish("workflow.goal_started", {
                "goal_id": str(goal.id), 
                "title": title,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return goal.id

    async def transition_phase(self, goal_id: UUID, target_state: WorkflowState) -> bool:
        """Attempts to move the goal to the next phase."""
        async with self.session_factory() as session:
            goal = await session.get(Goal, goal_id)
            if not goal:
                raise ValueError(f"Goal {goal_id} not found")
            
            # 1. Validate Transition
            current_state = WorkflowState(goal.status)
            validate_transition(current_state, target_state)
            
            # 2. Check Guards
            await check_guards(goal, target_state)
            
            # 3. Update State
            previous_state = current_state
            goal.status = target_state.value
            await session.commit()
            
            # 4. Trigger Entry Actions (Side effects)
            await self._on_enter_state(goal, target_state, previous_state)
            
            return True

    async def _on_enter_state(
        self, 
        goal: Goal, 
        state: WorkflowState, 
        previous_state: WorkflowState
    ) -> None:
        """Hook for side effects when entering a state."""
        await self.bus.publish("workflow.state_change", {
            "goal_id": str(goal.id),
            "previous_state": previous_state.value,
            "new_state": state.value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
