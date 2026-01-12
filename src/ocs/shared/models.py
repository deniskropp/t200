from enum import Enum, auto
from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AgentRole(str, Enum):
    DIRECTOR = "Director"
    LYRA = "Lyra"
    GPTASE = "GPTASe"
    TASE = "TASe"
    UTASE = "uTASe"
    PUTASE = "puTASe"
    AURORA = "Aurora"
    KODAX = "Kodax"
    DELIVERABLE_INTEGRATOR = "Deliverable_Integrator"
    USER = "User"
    SYSTEM = "System"

class TaskState(str, Enum):
    PENDING = "Pending"
    ACTIVE = "Active"
    COMPLETED = "Completed"
    FAILED = "Failed"

class KickLangSerializable(BaseModel):
    """Mixin to provide KickLang serialization capability."""
    model_config = ConfigDict(populate_by_name=True)

    def to_kicklang(self) -> str:
        # Placeholder for actual KickLang serialization logic
        # For now, it returns a primitive string representation
        return f"⫻data/{self.__class__.__name__.lower()}: {self.model_dump_json(indent=2)}"

class Task(KickLangSerializable):
    task_id: str
    subtask_of: Optional[str] = None
    owner: Optional[AgentRole] = None
    state: TaskState = TaskState.PENDING
    description: str
    output_ref: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)

class Phase(KickLangSerializable):
    phase_id: str
    name: str
    objectives: List[str]
    agents: List[AgentRole]
    active_tasks: List[str] = Field(default_factory=list, description="List of Task IDs")

class Communication(KickLangSerializable):
    actor: AgentRole
    recipient: AgentRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    phase_ref: Optional[str] = None
    message_type: str = "Directive"  # e.g., Directive, Report, Query
