import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Any, Final, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.bus.bus import MessageBus, MessageEnvelope
    from src.shared.models import AgentTask

from src.shared.models import AgentHeartbeat, AgentStatus, TaskState

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract Base Class for OCS Agents.
    Handles lifecycle, heartbeat, and task subscription.
    """

    HEARTBEAT_DEFAULT_INTERVAL: Final[float] = 5.0

    def __init__(
        self, 
        agent_id: str, 
        bus: "MessageBus", 
        heartbeat_interval: float = HEARTBEAT_DEFAULT_INTERVAL
    ) -> None:
        self.agent_id: str = agent_id
        self.bus: "MessageBus" = bus
        self.heartbeat_interval: float = heartbeat_interval
        self._status: AgentStatus = AgentStatus.IDLE
        self._current_task_id: Optional[str] = None
        self._shutdown_event: asyncio.Event = asyncio.Event()
        self._heartbeat_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Starts the agent's background processes."""
        logger.info("Agent %s starting...", self.agent_id)
        
        # Subscribe to own task queue
        await self.bus.subscribe(f"agents.{self.agent_id}.task", self._handle_task_envelope)
        
        # Start Heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._status = AgentStatus.IDLE
        await self._emit_heartbeat()

    async def stop(self) -> None:
        """Stops the agent gracefully."""
        logger.info("Agent %s stopping...", self.agent_id)
        self._shutdown_event.set()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
    async def _heartbeat_loop(self) -> None:
        """Periodically publishes heartbeat to the message bus."""
        while not self._shutdown_event.is_set():
            try:
                await self._emit_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in heartbeat loop for %s: %s", self.agent_id, e)
                await asyncio.sleep(5) # Backoff

    async def _emit_heartbeat(self) -> None:
        """Publishes the current agent status."""
        hb = AgentHeartbeat(
            agent_id=self.agent_id,
            status=self._status,
            current_task_id=self._current_task_id
        )
        await self.bus.publish("system.heartbeat", hb)

    async def log(self, level: str, message: str) -> None:
        """Helper to publish log events to the bus."""
        await self.bus.publish("agent.log", {
            "agent_id": self.agent_id,
            "level": level,
            "message": message
        })

    async def _handle_task_envelope(self, envelope: "MessageEnvelope") -> None:
        """Callback for incoming tasks from the message bus."""
        try:
            from src.shared.models import AgentTask
            
            data = envelope.payload
            if isinstance(data, dict):
                task = AgentTask(**data)
            elif isinstance(data, AgentTask):
                task = data
            else:
                logger.error("Invalid task payload received: %s", type(data))
                return

            await self._execute_task(task)

        except Exception as e:
            logger.error("Error handling task envelope: %s", e, exc_info=True)
            self._status = AgentStatus.ERROR

    async def _execute_task(self, task: "AgentTask") -> None:
        """Wraps the task processing with status updates and result reporting."""
        logger.info("Agent %s received task %s", self.agent_id, task.id)
        self._status = AgentStatus.WORKING
        self._current_task_id = task.id
        await self._emit_heartbeat()

        try:
            result = await self.process_task(task)
            
            # Standardize result publishing
            if result is not None:
                payload = {
                    "task_id": task.id,
                    "status": TaskState.COMPLETED.value,
                    "result": result,
                    "agent_id": self.agent_id
                }
                await self.bus.publish("workflow.task_result", payload, source_id=self.agent_id)
            
        except Exception as e:
            logger.error("Task %s failed: %s", task.id, e, exc_info=True)
            # Publish failure event to workflow
            await self.bus.publish("workflow.task_result", {
                "task_id": task.id,
                "status": TaskState.FAILED.value,
                "error": str(e),
                "agent_id": self.agent_id
            }, source_id=self.agent_id)
        finally:
            self._status = AgentStatus.IDLE
            self._current_task_id = None
            await self._emit_heartbeat()

    @abstractmethod
    async def process_task(self, task: "AgentTask") -> Any:
        """
        Business logic to process the task. 
        Must be implemented by subclasses.
        """
        pass
