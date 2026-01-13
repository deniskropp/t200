from typing import Annotated, List, Dict
from fastapi import APIRouter, Depends
from src.core.bus.bus import MessageBus, MessageEnvelope
from src.api.deps import get_bus
from src.shared.models import AgentHeartbeat

router = APIRouter()

# In-memory store for latest heartbeats (simple implementation for MVP)
_agent_registry: Dict[str, AgentHeartbeat] = {}

class AgentRegistryService:
    def __init__(self, bus: MessageBus):
        self.bus = bus
    
    async def start_listening(self) -> None:
        await self.bus.subscribe("system.heartbeat", self._update_heartbeat)

    async def _update_heartbeat(self, envelope: MessageEnvelope) -> None:
        """Update the internal registry with the latest heartbeat from an agent."""
        data = envelope.payload
        if isinstance(data, dict):
            # If payload is a dict, attempt to parse as AgentHeartbeat
            try:
                hb = AgentHeartbeat(**data)
            except Exception:
                # Fallback if parsing fails
                return
        elif isinstance(data, AgentHeartbeat):
            hb = data
        else:
            # Unsupported payload type
            return
        
        _agent_registry[hb.agent_id] = hb

@router.get("/")
async def list_agents(
    bus: Annotated[MessageBus, Depends(get_bus)]
) -> List[AgentHeartbeat]:
    """List all active agents seen recently."""
    return list(_agent_registry.values())
