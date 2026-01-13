import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Awaitable
from uuid import uuid4, UUID
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict

class MessageEnvelope(BaseModel):
    """Standard envelope for all messages on the bus."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    id: UUID = Field(default_factory=uuid4)
    topic: str
    payload: Any
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_id: str = "system"

class MessageBus(ABC):
    """Abstract Base Class for the Message Bus."""
    
    @abstractmethod
    async def publish(self, topic: str, payload: Any, source_id: str = "system") -> None:
        """Publish a message to a topic."""
        pass

    @abstractmethod
    async def subscribe(
        self, 
        topic: str, 
        callback: Callable[[MessageEnvelope], Awaitable[None]]
    ) -> None:
        """Subscribe to a topic with an async callback."""
        pass

class InMemoryMessageBus(MessageBus):
    """
    Simple in-memory implementation using asyncio. 
    Notes:
    - This is NOT durable. Messages are lost if process restarts.
    - Callbacks are executed concurrently in the background.
    """
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[MessageEnvelope], Awaitable[None]]]] = {}

    async def publish(self, topic: str, payload: Any, source_id: str = "system") -> None:
        """
        Publishes a message. Dispatches to all subscribers of the exact topic.
        Dispatch is non-blocking (fire-and-forget via asyncio.create_task).
        """
        envelope = MessageEnvelope(
            topic=topic,
            payload=payload,
            source_id=source_id
        )
        
        # Exact match for now
        if topic in self._subscribers:
            callbacks = self._subscribers[topic]
            for cb in callbacks:
                # Fire and forget callback execution
                asyncio.create_task(self._safe_dispatch(cb, envelope))

    async def _safe_dispatch(
        self, 
        callback: Callable[[MessageEnvelope], Awaitable[None]], 
        envelope: MessageEnvelope
    ) -> None:
        """Internal helper to execute callback and catch errors."""
        try:
            await callback(envelope)
        except Exception as e:
            # We use print here as logging might be circular or not configured in all contexts,
            # but usually we should use logger.
            import logging
            logging.getLogger(__name__).error("Error in bus callback for topic %s: %s", envelope.topic, e)

    async def subscribe(
        self, 
        topic: str, 
        callback: Callable[[MessageEnvelope], Awaitable[None]]
    ) -> None:
        """Adds a subscriber for a specific topic."""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
