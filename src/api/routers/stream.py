import asyncio
import logging
from typing import AsyncGenerator, Any
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from src.api.deps import get_bus
from src.core.bus.bus import MessageBus, MessageEnvelope

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stream")
async def sse_stream(request: Request) -> EventSourceResponse:
    """
    Server-Sent Events endpoint.
    Streams all bus messages to the client.
    """
    bus: MessageBus = get_bus()
    
    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        queue: asyncio.Queue[MessageEnvelope] = asyncio.Queue()
        
        async def handler(envelope: MessageEnvelope) -> None:
            await queue.put(envelope)
            
        # Subscribe to everything
        await bus.subscribe(".*", handler)
        
        try:
            while True:
                if await request.is_disconnected():
                    break
                
                envelope = await queue.get()
                yield {
                    "event": "message",
                    "data": {
                        "topic": envelope.topic,
                        "payload": envelope.payload,
                        "timestamp": envelope.timestamp.isoformat(),
                        "source": envelope.source_id
                    }
                }
        except asyncio.CancelledError:
            logger.info("SSE client disconnected")
        finally:
            # Cleanup - in robust system we'd unsubscribe
            pass
            
    return EventSourceResponse(event_generator())
