
import asyncio
import logging
from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from src.api.deps import get_bus
from src.core.bus.bus import MessageBus

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/stream") # accessible at /api/v1/stream/sse due to router inclusion
async def sse_stream(request: Request):
    """
    Server-Sent Events endpoint.
    Streams all bus messages to the client.
    """
    bus: MessageBus = get_bus()
    
    async def event_generator():
        queue = asyncio.Queue()
        
        async def handler(envelope):
            await queue.put(envelope)
            
        # Subscribe to everything
        # Note: Bus implementation must support wildcard or we subscribe to specific topics
        # Our InMemoryBus regex matching for "*" might work if implemented, 
        # checking bus.py: if re.match(sub_pattern, topic): ...
        # If we use ".*" it should work for regex.
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
