
import logging
import asyncio
import json
from uuid import UUID
from typing import Any

from src.core.agents.base import BaseAgent
from src.core.bus.bus import MessageBus, MessageEnvelope
from src.core.db.session import AsyncSessionLocal
from src.core.db.models import Task, Goal

logger = logging.getLogger(__name__)

from typing import Optional, List
from pydantic import BaseModel
from src.core.llm.service import LLMService

class TaskModel(BaseModel):
    title: str
    type: str # RESEARCH, DESIGN, CODING
    description: str

class TaskDecompositionSchema(BaseModel):
    tasks: List[TaskModel]

class LyraAgent(BaseAgent):
    """
    Lyra: The Prompt Engineer & Task Decomposer.
    Responsible for breaking down High-Level Goals into executable Tasks.
    """
    def __init__(self, bus: MessageBus, llm: LLMService = None, session_factory=AsyncSessionLocal):
        super().__init__(agent_id="Lyra", bus=bus)
        self.session_factory = session_factory
        self.llm = llm

    async def start(self):
        await super().start()
        # Listen for specific delegation commands
        await self.bus.subscribe("agent.lyra.decompose", self.on_decompose_request)

    async def process_task(self, task: Any) -> Any:
        return {"status": "ok"}

    async def on_decompose_request(self, envelope: MessageEnvelope):
        """
        Handles request to decompose a goal.
        Payload: { "goal_id": str, "title": str, "description": str }
        """
        payload = envelope.payload
        goal_id_str = payload.get("goal_id")
        title = payload.get("title")
        description = payload.get("description", "")
        
        logger.info(f"Lyra received decomposition request for goal: {title} ({goal_id_str})")
        
        await self.bus.publish("agent.log", {
            "agent_id": self.agent_id,
            "level": "INFO",
            "message": f"Starting task decomposition for '{title}'..."
        })

        # Generate Tasks using LLM
        generated_tasks_data = []
        if self.llm:
            try:
                system_instruction = (
                    "You are Lyra, a task decomposition expert. "
                    "Break down the following goal into 3-5 distinct, executable technical tasks. "
                    "Types: RESEARCH, DESIGN, CODING, REVIEW. "
                    "Return JSON matching the schema."
                )
                prompt = f"Goal: {title}\nContext: {description}\n{system_instruction}"
                
                await self.bus.publish("agent.log", {
                    "agent_id": self.agent_id,
                    "level": "INFO",
                    "message": "Consulting Gemini..."
                })

                # Call LLM
                response = await self.llm.generate(prompt, schema=TaskDecompositionSchema)
                if response and hasattr(response, 'tasks'):
                    generated_tasks_data = response.tasks
                elif isinstance(response, dict) and 'tasks' in response:
                    generated_tasks_data = [TaskModel(**t) for t in response['tasks']]
                
                await self.bus.publish("agent.log", {
                    "agent_id": self.agent_id,
                    "level": "SUCCESS",
                    "message": "Gemini generated tasks."
                })

            except Exception as e:
                 logger.error(f"Lyra LLM generation failed: {e}")
                 # Fallback
                 generated_tasks_data = [
                      TaskModel(title="Research (Fallback)", type="RESEARCH", description="Investigation needed due to LLM error.")
                 ]
        else:
             # Fallback if no LLM service
             generated_tasks_data = [
                TaskModel(title=f"Research {title}", type="RESEARCH", description="Default task"),
                TaskModel(title=f"Implement {title}", type="CODING", description="Default task")
             ]

        # 2. Persist to DB
        try:
            async with self.session_factory() as session:
                # verify goal exists
                goal = await session.get(Goal, UUID(goal_id_str))
                if not goal:
                    logger.error(f"Goal {goal_id_str} not found during decomposition.")
                    return

                created_tasks = []
                for t_model in generated_tasks_data:
                    new_task = Task(
                        goal_id=goal.id,
                        title=t_model.title,
                        type=t_model.type,
                        payload={"description": t_model.description},
                        assigned_to=None # Pending assignment
                    )
                    session.add(new_task)
                    created_tasks.append(new_task)
                
                await session.commit()
                
                logger.info(f"Lyra created {len(created_tasks)} tasks for goal {goal_id_str}")
                
                await self.bus.publish("agent.log", {
                    "agent_id": self.agent_id,
                    "level": "SUCCESS",
                    "message": f"Decomposed goal into {len(created_tasks)} tasks."
                })
                
                # Publish event so others know tasks are ready
                await self.bus.publish("workflow.tasks_generated", {
                    "goal_id": goal_id_str,
                    "task_count": len(created_tasks)
                })
                
        except Exception as e:
            logger.error(f"Lyra failed to save tasks: {e}", exc_info=True)
            await self.bus.publish("agent.log", {
                "agent_id": self.agent_id,
                "level": "ERROR",
                "message": f"Failed to save tasks: {str(e)}"
            })
