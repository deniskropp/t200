import logging
import asyncio
from typing import Any, TYPE_CHECKING
from uuid import UUID

from src.core.agents.base import BaseAgent
from src.core.workflow.state import WorkflowState
from src.shared.models import AgentRole, TaskState

if TYPE_CHECKING:
    from src.core.bus.bus import MessageEnvelope, MessageBus
    from src.core.workflow.engine import WorkflowEngine
    from src.shared.models import AgentTask

logger = logging.getLogger(__name__)

class DirectorAgent(BaseAgent):
    """
    The Director Agent orchestrates the high-level workflow of the OCS.
    It listens for system events and decides when to advance phases.
    """
    def __init__(self, bus: "MessageBus", engine: "WorkflowEngine") -> None:
        super().__init__(agent_id=AgentRole.DIRECTOR.value, bus=bus)
        self.engine: "WorkflowEngine" = engine

    async def process_task(self, task: "AgentTask") -> Any:
        # Director might process explicit tasks too
        logger.info("Director processing task: %s", task.type)
        return {"status": "ok", "msg": "Director processed task"}

    async def on_goal_started(self, envelope: "MessageEnvelope") -> None:
        """
        Reacts to a new goal being created.
        Currently, it automatically approves the transition to Task Decomposition (Phase 2).
        """
        data = envelope.payload
        goal_id = data.get("goal_id")
        title = data.get("title")
        
        if not goal_id or not title:
            logger.warning("Incomplete goal_started event received: %s", data)
            return

        logger.info("Director observed new goal: %s (%s). Initiating assessment.", title, goal_id)
        await self.log("INFO", f"Observed new goal: '{title}'. Assessing feasibility...")
        
        # Simulate thinking/processing time (e.g., calling LLM for feasibility)
        await asyncio.sleep(2) 
        
        # Attempt to transition to Phase 2
        try:
            logger.info("Director approving transition to Task Decomposition for %s", goal_id)
            await self.log("INFO", f"Goal '{title}' approved. Transitioning to Task Decomposition.")
            await self.engine.transition_phase(UUID(goal_id), WorkflowState.TASK_DECOMPOSITION)
        except Exception as e:
            logger.error("Director failed to transition goal %s: %s", goal_id, e)

    async def on_state_change(self, envelope: "MessageEnvelope") -> None:
        """
        Reacts to state transitions.
        """
        data = envelope.payload
        new_state = data.get("new_state")
        goal_id = data.get("goal_id")
        
        logger.info("Director observed state change for %s -> %s", goal_id, new_state)
        
        if new_state == WorkflowState.TASK_DECOMPOSITION.value:
            logger.info("Director is now searching for Lyra to delegate Prompt Engineering...")
            await self.log("INFO", "Phase Task Decomposition active. Delegating to Lyra...")
            
            # Fetch Goal details to pass to Lyra
            from src.core.db.models import Goal
            
            try:
                # Use engine's session factory
                async with self.engine.session_factory() as session:
                    goal = await session.get(Goal, UUID(goal_id))
                    if goal:
                        # Delegate to Lyra
                        await self.bus.publish("agent.lyra.decompose", {
                            "goal_id": goal_id,
                            "title": goal.title,
                            "description": goal.description
                        })
                        logger.info("Delegated goal %s to Lyra.", goal.title)
            except Exception as e:
                logger.error("Director failed to delegate to Lyra: %s", e)

    async def on_tasks_generated(self, envelope: "MessageEnvelope") -> None:
        """
        Reacts when Lyra (or others) generate tasks.
        Assigns these tasks to GPTASe for execution.
        """
        data = envelope.payload
        goal_id = data.get("goal_id")
        count = data.get("task_count")
        
        logger.info("Director observed %s new tasks for goal %s. Assigning to GPTASe.", count, goal_id)
        await self.log("INFO", f"Found {count} pending tasks. Assigning to Agents...")
        
        from src.core.db.models import Task
        from sqlalchemy import select
        
        try:
            async with self.engine.session_factory() as session:
                # 1. Fetch unassigned tasks
                result = await session.execute(
                    select(Task).where(Task.goal_id == UUID(goal_id), Task.status == TaskState.PENDING.value)
                )
                tasks = result.scalars().all()
                
                for task in tasks:
                    # 2. Assign to GPTASe (Logic would be more complex in real system)
                    task.assigned_to = AgentRole.GPTASE.value
                    task.status = TaskState.ACTIVE.value
                    session.add(task)
                    
                    # 3. Publish Assignment
                    agent_task_payload = {
                        "id": str(task.id),
                        "type": task.type,
                        "title": task.title,
                        "payload": task.payload,
                        "assigned_to": AgentRole.GPTASE.value
                    }
                    
                    await self.bus.publish(f"agents.{AgentRole.GPTASE.value}.task", agent_task_payload)
                    await self.log("INFO", f"Assigned task '{task.title}' to {AgentRole.GPTASE.value}.")
                
                await session.commit()
                
        except Exception as e:
            logger.error("Director failed to assign tasks: %s", e, exc_info=True)

    async def on_task_result(self, envelope: "MessageEnvelope") -> None:
        """
        Reacts to task results.
        Updates DB status.
        """
        data = envelope.payload
        task_id = data.get("task_id")
        status = data.get("status")
        result_payload = data.get("result")
        
        logger.info("Director processing result for task %s: %s", task_id, status)
        
        from src.core.db.models import Task
        
        try:
            async with self.engine.session_factory() as session:
                task = await session.get(Task, UUID(task_id))
                if task:
                    task.status = status
                    task.result = {"output": result_payload}
                    session.add(task)
                    await session.commit()
                    
                    logger.info("Task %s marked as %s in DB.", task.title, status)
                    await self.log("INFO", f"Updated Task '{task.title}' status to {status}.")
        except Exception as e:
            logger.error("Director failed to process task result: %s", e, exc_info=True)

    async def start(self) -> None:
        await super().start()
        # Subscribe to workflow events
        await self.bus.subscribe("workflow.goal_started", self.on_goal_started)
        await self.bus.subscribe("workflow.state_change", self.on_state_change)
        await self.bus.subscribe("workflow.tasks_generated", self.on_tasks_generated)
        await self.bus.subscribe("workflow.task_result", self.on_task_result)
