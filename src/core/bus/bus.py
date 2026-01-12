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
    async def subscribe(self, topic: str, callback: Callable[[MessageEnvelope], Awaitable[None]]) -> None:
        """Subscribe to a topic with an async callback."""
        pass

class InMemoryMessageBus(MessageBus):
    """
    Simple in-memory implementation using asyncio. 
    Notes:
    - This is NOT durable. Messages are lost if process restarts.
    - Callbacks are executed concurrently but awaiting completion in publish is optional 
      depending on desired behavior. For now, we'll fire-and-forget (background task) 
      or gather? 
      Strictly for an Event Bus, fire-and-forget is common, but for correct ordering 
      we might want to be careful.
      
      Let's implement a simple direct-dispatch first (synchronous dispatch in async context)
      so the publisher knows it was delivered to the loop, but maybe not fully processed.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[MessageEnvelope], Awaitable[None]]]] = {}

    async def publish(self, topic: str, payload: Any, source_id: str = "system") -> None:
        envelope = MessageEnvelope(
            topic=topic,
            payload=payload,
            source_id=source_id
        )
        
        # Exact match for now (no wildcards yet)
        if topic in self._subscribers:
            callbacks = self._subscribers[topic]
            # Fire and forget: Do not await completion here.
            # This mimics real async bus behavior (eventual consistency).
            if callbacks:
                for cb in callbacks:
                    asyncio.create_task(cb(envelope))

    async def subscribe(self, topic: str, callback: Callable[[MessageEnvelope], Awaitable[None]]) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)
