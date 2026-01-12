from typing import Annotated, List, Dict
from fastapi import APIRouter, Depends
from src.core.bus.bus import MessageBus
from src.api.deps import get_bus
from src.shared.models import AgentHeartbeat

router = APIRouter()

# In-memory store for latest heartbeats (simple implementation for MVP)
# In real system, this would read from Redis or a dedicated Service
_agent_registry: Dict[str, AgentHeartbeat] = {}

class AgentRegistryService:
    def __init__(self, bus: MessageBus):
        self.bus = bus
    
    async def start_listening(self):
        await self.bus.subscribe("system.heartbeat", self._update_heartbeat)

    async def _update_heartbeat(self, envelope):
        # Assuming payload is dict or model
        data = envelope.payload
        if isinstance(data, dict):
            hb = AgentHeartbeat(**data)
        else:
            hb = data
        _agent_registry[hb.agent_id] = hb

@router.get("/")
async def list_agents(
    bus: Annotated[MessageBus, Depends(get_bus)]
) -> List[AgentHeartbeat]:
    """List all active agents seen recently."""
    # Note: This requires the registry listener to be active. 
    # For MVP, we might assume there's a background service updating this.
    # For now, just return valid registry states.
    return list(_agent_registry.values())
