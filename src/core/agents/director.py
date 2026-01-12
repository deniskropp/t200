
import logging
import asyncio
from typing import Any
from src.core.agents.base import BaseAgent
from src.core.workflow.engine import WorkflowEngine
from src.core.workflow.state import WorkflowState
from src.ocs.shared.models import AgentTask
from src.core.bus.bus import MessageEnvelope, MessageBus

logger = logging.getLogger(__name__)

class DirectorAgent(BaseAgent):
    """
    The Director Agent orchestrates the high-level workflow of the OCS.
    It listens for system events and decides when to advance phases.
    """
    def __init__(self, bus: MessageBus, engine: WorkflowEngine):
        super().__init__(agent_id="Director", bus=bus)
        self.engine = engine

    async def start(self):
        await super().start()
        # Subscribe to workflow events
        await self.bus.subscribe("workflow.goal_started", self.on_goal_started)
        await self.bus.subscribe("workflow.state_change", self.on_state_change)

    async def process_task(self, task: AgentTask) -> Any:
        # Director might process explicit tasks too
        logger.info(f"Director processing task: {task.type}")
        return {"status": "ok", "msg": "Director processed task"}

    async def on_goal_started(self, envelope: MessageEnvelope):
        """
        Reacts to a new goal being created.
        Currently, it automatically approves the transition to Task Decomposition (Phase 2).
        """
        data = envelope.payload
        # Payload might be dict from pydantic serialization
        goal_id = data.get("goal_id")
        title = data.get("title")
        
        logger.info(f"Director observed new goal: {title} ({goal_id}). Initiating assessment.")
        await self.bus.publish("agent.log", {
            "agent_id": "Director", 
            "level": "INFO", 
            "message": f"Observed new goal: '{title}'. Assessing feasibility..."
        })
        
        # Simulate thinking/processing time (e.g., calling LLM for feasibility)
        await asyncio.sleep(2) 
        
        # Attempt to transition to Phase 2
        try:
            logger.info(f"Director approving transition to Task Decomposition for {goal_id}")
            await self.bus.publish("agent.log", {
                "agent_id": "Director", 
                "level": "INFO", 
                "message": f"Goal '{title}' approved. Transitioning to Task Decomposition."
            })
            # Note: goal_id in payload is str, transition_phase expects UUID or str? 
            # engine.transition_phase expects UUID according to type hint, but usually asyncpg/sqlalchemy handle strings if mapped to UUID.
            # However, looking at engine.py: async def transition_phase(self, goal_id: UUID, ...)
            # We should probably cast it to UUID to be safe, or ensure engine handles it.
            # Let's import UUID.
            from uuid import UUID
            await self.engine.transition_phase(UUID(goal_id), WorkflowState.TASK_DECOMPOSITION)
        except Exception as e:
            logger.error(f"Director failed to transition goal {goal_id}: {e}")

    async def on_state_change(self, envelope: MessageEnvelope):
        """
        Reacts to state transitions.
        """
        data = envelope.payload
        new_state = data.get("new_state")
        goal_id = data.get("goal_id")
        
        logger.info(f"Director observed state change for {goal_id} -> {new_state}")
        
        if new_state == WorkflowState.TASK_DECOMPOSITION.value:
            logger.info("Director is now searching for Lyra to delegate Prompt Engineering...")
            await self.bus.publish("agent.log", {
                "agent_id": "Director", 
                "level": "INFO", 
                "message": f"Phase Task Decomposition active. Delegating to Lyra..."
            })
            
            # Fetch Goal details to pass to Lyra
            from src.core.db.models import Goal
            from uuid import UUID
            
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
                        logger.info(f"Delegated goal {goal.title} to Lyra.")
            except Exception as e:
                logger.error(f"Director failed to delegate to Lyra: {e}")

    async def on_tasks_generated(self, envelope: MessageEnvelope):
        """
        Reacts when Lyra (or others) generate tasks.
        Assigns these tasks to GPTASe for execution.
        """
        data = envelope.payload
        goal_id = data.get("goal_id")
        count = data.get("task_count")
        
        logger.info(f"Director observed {count} new tasks for goal {goal_id}. Assigning to GPTASe.")
        
        await self.bus.publish("agent.log", {
            "agent_id": "Director", 
            "level": "INFO", 
            "message": f"Found {count} pending tasks. Assigning to Agents..."
        })
        
        from src.core.db.models import Task
        from sqlalchemy import select, update
        from uuid import UUID
        
        try:
            async with self.engine.session_factory() as session:
                # 1. Fetch unassigned tasks
                result = await session.execute(
                    select(Task).where(Task.goal_id == UUID(goal_id), Task.status == "PENDING")
                )
                tasks = result.scalars().all()
                
                for task in tasks:
                    # 2. Assign to GPTASe (Logic would be more complex in real system)
                    # Update DB
                    task.assigned_to = "GPTASe"
                    task.status = "IN_PROGRESS"
                    session.add(task)
                    
                    # 3. Publish Assignment
                    # Convert to AgentTask model for transport
                    agent_task_payload = {
                        "id": str(task.id),
                        "type": task.type,
                        "title": task.title,
                        "payload": task.payload
                    }
                    
                    await self.bus.publish(f"agents.GPTASe.task", agent_task_payload)
                    
                    await self.bus.publish("agent.log", {
                        "agent_id": "Director",
                        "level": "INFO",
                        "message": f"Assigned task '{task.title}' to GPTASe."
                    })
                
                await session.commit()
                
        except Exception as e:
            logger.error(f"Director failed to assign tasks: {e}", exc_info=True)

    async def on_task_result(self, envelope: MessageEnvelope):
        """
        Reacts to task results.
        Updates DB status.
        """
        data = envelope.payload
        task_id = data.get("task_id")
        status = data.get("status")
        result_payload = data.get("result")
        
        logger.info(f"Director processing result for task {task_id}: {status}")
        
        from src.core.db.models import Task
        from uuid import UUID
        
        try:
            async with self.engine.session_factory() as session:
                task = await session.get(Task, UUID(task_id))
                if task:
                    task.status = status
                    task.result = {"output": result_payload}
                    session.add(task)
                    await session.commit()
                    
                    logger.info(f"Task {task.title} marked as {status} in DB.")
                    await self.bus.publish("agent.log", {
                        "agent_id": "Director",
                        "level": "INFO",
                        "message": f"Updated Task '{task.title}' status to {status}."
                    })
        except Exception as e:
            logger.error(f"Director failed to process task result: {e}", exc_info=True)

    async def start(self):
        await super().start()
        # Subscribe to workflow events
        await self.bus.subscribe("workflow.goal_started", self.on_goal_started)
        await self.bus.subscribe("workflow.state_change", self.on_state_change)
        await self.bus.subscribe("workflow.tasks_generated", self.on_tasks_generated)
        await self.bus.subscribe("workflow.task_result", self.on_task_result)
