import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Coroutine
from uuid import UUID

from src.core.bus.bus import MessageBus, MessageEnvelope
from src.shared.models import AgentTask, AgentHeartbeat, AgentStatus

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """
    Abstract Base Class for OCS Agents.
    Handles lifecycle, heartbeat, and task subscription.
    """

    def __init__(self, agent_id: str, bus: MessageBus, heartbeat_interval: float = 5.0):
        self.agent_id = agent_id
        self.bus = bus
        self.heartbeat_interval = heartbeat_interval
        self._status = AgentStatus.IDLE
        self._current_task_id: Optional[str] = None
        self._shutdown_event = asyncio.Event()
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def start(self):
        """Starts the agent's background processes."""
        logger.info(f"Agent {self.agent_id} starting...")
        
        # Subscribe to own task queue
        await self.bus.subscribe(f"agents.{self.agent_id}.task", self._handle_task_envelope)
        
        # Start Heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._status = AgentStatus.IDLE
        await self._emit_heartbeat()

    async def stop(self):
        """Stops the agent."""
        logger.info(f"Agent {self.agent_id} stopping...")
        self._shutdown_event.set()
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
    async def _heartbeat_loop(self):
        """Periodically publishes heartbeat."""
        while not self._shutdown_event.is_set():
            try:
                await self._emit_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop for {self.agent_id}: {e}")
                await asyncio.sleep(5) # Backoff

    async def _emit_heartbeat(self):
        hb = AgentHeartbeat(
            agent_id=self.agent_id,
            status=self._status,
            current_task_id=self._current_task_id
        )
        await self.bus.publish("system.heartbeat", hb)

    async def log(self, level: str, message: str):
        """Helper to publish log events."""
        await self.bus.publish("agent.log", {
            "agent_id": self.agent_id,
            "level": level,
            "message": message
        })

    async def _handle_task_envelope(self, envelope: MessageEnvelope):
        """Callback for incoming tasks."""
        try:
            # Parse payload to AgentTask
            # Assuming payload is dict or AgileTask object. 
            # If it comes from pydantic dump, it might be dict.
            data = envelope.payload
            if isinstance(data, dict):
                task = AgentTask(**data)
            elif isinstance(data, AgentTask):
                task = data
            else:
                logger.error(f"Invalid task payload received: {type(data)}")
                return

            await self._execute_task(task)

        except Exception as e:
            logger.error(f"Error handling task envelope: {e}", exc_info=True)
            self._status = AgentStatus.ERROR

    async def _execute_task(self, task: AgentTask):
        """Wraps the task processing with status updates."""
        logger.info(f"Agent {self.agent_id} received task {task.id}")
        self._status = AgentStatus.WORKING
        self._current_task_id = task.id
        await self._emit_heartbeat()

        try:
            result = await self.process_task(task)
            # Standardize result publishing
            # If process_task returns a dict, assume it's the result.
            # Only publish if result is not None (allows agents to opt-out or handle it themselves if they return None)
            if result is not None:
                payload = {
                    "task_id": task.id,
                    "status": "COMPLETED",
                    "result": result, # Can be dict or string
                    "agent_id": self.agent_id
                }
                await self.bus.publish("workflow.task_result", payload, source_id=self.agent_id)
            
        except Exception as e:
            logger.error(f"Task {task.id} failed: {e}", exc_info=True)
            # Publish failure event to workflow
            await self.bus.publish("workflow.task_result", {
                "task_id": task.id,
                "status": "FAILED",
                "error": str(e),
                "agent_id": self.agent_id
            }, source_id=self.agent_id)
        finally:
            self._status = AgentStatus.IDLE
            self._current_task_id = None
            await self._emit_heartbeat()

    @abstractmethod
    async def process_task(self, task: AgentTask) -> Any:
        """
        Business logic to process the task. 
        Must be implemented by subclasses.
        """
        pass
