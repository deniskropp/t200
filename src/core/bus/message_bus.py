import asyncio
from typing import Dict, Set, Callable, Awaitable
from src.core.agents.base import AgentTask

# Type alias for subscribers
Subscriber = Callable[[AgentTask], Awaitable[None]]

class MessageBus:
    def __init__(self):
        self._queues: Dict[str, asyncio.Queue] = {}
        self._subscribers: Dict[str, Set[Subscriber]] = {}

    def get_queue(self, agent_id: str) -> asyncio.Queue:
        if agent_id not in self._queues:
            self._queues[agent_id] = asyncio.Queue()
        return self._queues[agent_id]

    async def publish(self, topic: str, message: AgentTask):
        """Publish a message to a specific agent's queue or topic."""
        # 1. Direct Queue (if topic matches an Agent ID)
        if topic in self._queues:
            await self._queues[topic].put(message)
        
        # 2. General Subscribers (Mock pub/sub logic for now)
        if topic in self._subscribers:
            for handler in self._subscribers[topic]:
                asyncio.create_task(handler(message))

    def subscribe(self, topic: str, handler: Subscriber):
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
        self._subscribers[topic].add(handler)

# Global singleton for Monolith MVP
bus = MessageBus()
