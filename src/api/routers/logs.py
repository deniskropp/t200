import asyncio
from typing import Annotated, List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.core.bus.bus import MessageBus, MessageEnvelope
from src.api.deps import get_bus

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    bus: Annotated[MessageBus, Depends(get_bus)]
) -> None:
    await websocket.accept()
    
    # Bridge: Listen to bus, send to WS
    queue: asyncio.Queue[MessageEnvelope] = asyncio.Queue()
    
    async def bridge_callback(envelope: MessageEnvelope) -> None:
        await queue.put(envelope)
        
    # Subscribe to critical topics for the log viewer
    critical_topics: List[str] = [
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
        pass
