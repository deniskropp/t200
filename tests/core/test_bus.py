import pytest
import asyncio
from src.core.bus.bus import InMemoryMessageBus, MessageEnvelope

@pytest.mark.asyncio
async def test_bus_publish_subscribe():
    bus = InMemoryMessageBus()
    received = []

    async def callback(envelope: MessageEnvelope):
        received.append(envelope)

    await bus.subscribe("test.topic", callback)
    
    await bus.publish("test.topic", {"data": "hello"})
    
    # Allow loop to process
    await asyncio.sleep(0.1)
    
    assert len(received) == 1
    assert received[0].topic == "test.topic"
    assert received[0].payload == {"data": "hello"}

@pytest.mark.asyncio
async def test_bus_multiple_subscribers():
    bus = InMemoryMessageBus()
    count = 0

    async def cb1(env):
        nonlocal count
        count += 1
        
    async def cb2(env):
        nonlocal count
        count += 2

    await bus.subscribe("event", cb1)
    await bus.subscribe("event", cb2)
    
    await bus.publish("event", {})
    await asyncio.sleep(0.1)
    
    assert count == 3
