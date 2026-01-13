from enum import Enum
from typing import List, Optional, Any, Dict
from datetime import datetime, timezone
from uuid import uuid4
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

class AgentStatus(str, Enum):
    IDLE = "Idle"
    WORKING = "Working"
    ERROR = "Error"
    STALLED = "Stalled"

class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phase_ref: Optional[str] = None
    message_type: str = "Directive"  # e.g., Directive, Report, Query

class TaskConstraints(BaseModel):
    timeout_seconds: float = 300.0
    max_retries: int = 3
    required_capabilities: List[str] = Field(default_factory=list)

class AgentTask(KickLangSerializable):
    """Payload sent to an agent to perform a specific action."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str # e.g. "generation", "review"
    title: str = "" 
    payload: Dict[str, Any]
    context_refs: List[str] = Field(default_factory=list)
    constraints: TaskConstraints = Field(default_factory=TaskConstraints)
    assigned_to: str # AgentID
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AgentHeartbeat(BaseModel):
    agent_id: str
    status: AgentStatus
    current_task_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

