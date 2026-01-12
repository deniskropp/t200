from typing import Annotated, AsyncGenerator
from fastapi import Depends
from src.core.bus.bus import MessageBus, InMemoryMessageBus
from src.core.workflow.engine import WorkflowEngine
from src.core.db.session import AsyncSessionLocal

from src.core.llm.service import LLMService

# Global Singletons
_bus: MessageBus = InMemoryMessageBus()
_engine: WorkflowEngine = WorkflowEngine(bus=_bus, session_factory=AsyncSessionLocal)
_llm: LLMService = LLMService()

def get_bus() -> MessageBus:
    return _bus

def get_engine() -> WorkflowEngine:
    return _engine

def get_llm() -> LLMService:
    return _llm
