import pytest
import asyncio
from typing import Any
from src.core.agents.base import BaseAgent
from src.core.bus.bus import InMemoryMessageBus, MessageEnvelope
from src.ocs.shared.models import AgentTask, AgentStatus

class MockAgent(BaseAgent):
    def __init__(self, agent_id, bus):
        super().__init__(agent_id, bus, heartbeat_interval=0.1)
        self.processed = []

    async def process_task(self, task: AgentTask) -> Any:
        self.processed.append(task)
        return "processed"

@pytest.mark.asyncio
async def test_agent_lifecycle():
    bus = InMemoryMessageBus()
    agent = MockAgent("test-agent", bus)
    
    # Capture heartbeats
    heartbeats = []
    async def hb_cb(env: MessageEnvelope):
        heartbeats.append(env.payload)
    await bus.subscribe("system.heartbeat", hb_cb)

    await agent.start()
    await asyncio.sleep(0.15) # Wait for initial + 1 heartbeat
    
    await agent.stop()
    
    assert len(heartbeats) >= 2
    assert heartbeats[0].agent_id == "test-agent"
    assert heartbeats[0].status == AgentStatus.IDLE

@pytest.mark.asyncio
async def test_agent_task_execution():
    bus = InMemoryMessageBus()
    agent = MockAgent("worker", bus)
    await agent.start()

    # Create task
    task = AgentTask(
        type="test",
        payload={"foo": "bar"},
        assigned_to="worker"
    )

    # Listen for result
    results = []
    async def res_cb(env):
        results.append(env.payload)
    await bus.subscribe(f"tasks.{task.id}.result", res_cb)

    # Publish task to agent's queue
    await bus.publish(f"agents.worker.task", task)
    
    await asyncio.sleep(0.2)
    
    assert len(agent.processed) == 1
    assert agent.processed[0].id == task.id
    
    assert len(results) == 1
    assert results[0]["status"] == "success"
    assert results[0]["result"] == "processed"

    await agent.stop()
