import logging
import asyncio
import random
from typing import Any, Optional, TYPE_CHECKING
from src.core.agents.base import BaseAgent
from src.shared.models import AgentRole

if TYPE_CHECKING:
    from src.core.bus.bus import MessageBus
    from src.shared.models import AgentTask
    from src.core.llm.service import LLMService

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class TaskResultSchema(BaseModel):
    summary: str
    output: str

class GPTASeAgent(BaseAgent):
    """
    GPTASe: General Purpose Task Agent.
    Executes specific sub-tasks assigned by the Director.
    """
    def __init__(
        self, 
        bus: "MessageBus", 
        llm: Optional["LLMService"] = None
    ) -> None:
        super().__init__(agent_id=AgentRole.GPTASE.value, bus=bus)
        self.llm = llm

    async def process_task(self, task: "AgentTask") -> Any:
        """
        Executes task using LLM.
        """
        logger.info("GPTASe executing task: %s (%s)", task.title, task.id)
        await self.log("INFO", f"Starting execution of '{task.title}'...")

        output_content = ""
        summary = ""

        if self.llm:
            try:
                system_prompt = (
                    "You are GPTASe, an expert autonomous agent. "
                    "Execute the assigned task strictly based on the inputs. "
                    "Provide a summary and the detailed output."
                )
                user_prompt = f"Task: {task.title}\nDetails: {task.payload}"
                
                await self.log("INFO", "Consulting Gemini...")

                response = await self.llm.generate(
                    f"{system_prompt}\n{user_prompt}", 
                    schema=TaskResultSchema
                )
                
                if response:
                    # Handle both obj (if parsed) or dict
                    if isinstance(response, TaskResultSchema):
                         summary = response.summary
                         output_content = response.output
                    elif isinstance(response, dict):
                         summary = str(response.get('summary', ''))
                         output_content = str(response.get('output', ''))
                    else:
                         output_content = str(response)
                         summary = "Generated content."

                await self.log("SUCCESS", "Gemini completed task.")

            except Exception as e:
                logger.error("GPTASe LLM failed: %s", e)
                summary = "Failed to execute via LLM"
                output_content = str(e)
                raise e 
        else:
             await asyncio.sleep(random.uniform(1.0, 2.0))
             summary = f"Executed {task.title}"
             output_content = "Mock output content."

        result = f"{summary} | {output_content[:50]}..."
        await self.log("SUCCESS", f"Completed '{task.title}'.")
        
        return result
