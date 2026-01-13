from src.core.bus.bus import MessageBus, InMemoryMessageBus
from src.core.workflow.engine import WorkflowEngine
from src.core.db.session import AsyncSessionLocal

from src.core.llm.service import LLMService

# Global Singletons
_bus: MessageBus = InMemoryMessageBus()
_engine: WorkflowEngine = WorkflowEngine(bus=_bus, session_factory=AsyncSessionLocal)
_llm: LLMService = LLMService()

def get_bus() -> MessageBus:
    """Provides the singular message bus instance."""
    return _bus

def get_engine() -> WorkflowEngine:
    """Provides the singular workflow engine instance."""
    return _engine

def get_llm() -> LLMService:
    """Provides the singular LLM service instance."""
    return _llm
