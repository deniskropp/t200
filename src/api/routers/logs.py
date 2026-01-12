from typing import Annotated
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.core.bus.bus import MessageBus, MessageEnvelope
from src.api.deps import get_bus

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    bus: Annotated[MessageBus, Depends(get_bus)]
):
    await websocket.accept()
    
    # Bridge: Listen to bus, send to WS
    # Note: In a real app, we need a way to unsubscribe when WS disconnects.
    # The InMemoryBus might accumulate callbacks if we aren't careful.
    # For MVP, we'll use a queue-based bridge per connection? 
    # Or just a persistent callback that checks generic connection state.
    # Better: use asyncio.Queue for this connection.
    
    import asyncio
    queue = asyncio.Queue()
    
    async def bridge_callback(envelope: MessageEnvelope):
        await queue.put(envelope)
        
    # Subscribe to EVERYTHING for the log viewer
    # (Assuming bus supports wildcard or we subscribe to specific known topics)
    # Our InMemoryBus doesn't support wildcards yet. 
    # Let's fix that or subscribe to critical ones for now.
    critical_topics = [
        "workflow.goal_started",
        "workflow.state_change",
        "system.heartbeat",
        "agent.log"
    ]
    
    for topic in critical_topics:
        await bus.subscribe(topic, bridge_callback)
        
    try:
        while True:
            # Wait for message from bus
            envelope = await queue.get()
            
            # Send to WS
            await websocket.send_json({
                "topic": envelope.topic,
                "payload": envelope.payload,
                "timestamp": envelope.timestamp.isoformat(),
                "source": envelope.source_id
            })
    except WebSocketDisconnect:
        # Cleanup: In a real implementation, we'd remove the callback from the bus.
        # But our InMemoryBus doesn't have unsubscribe yet. 
        # For MVP/Prototype, this leak is acceptable but noted.
        pass
