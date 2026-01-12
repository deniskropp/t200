from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import AgentRole, Communication, Task

class AgentProtocol(ABC):
    """
    Abstract Base Class allowing different implementations of Agents 
    (e.g., LLM-based, Rule-based, or Human-in-the-loop).
    """

    def __init__(self, role: AgentRole):
        self.role = role

    @property
    @abstractmethod
    def data_in(self) -> List[str]:
        """List of expected data input types."""
        pass

    @property
    @abstractmethod
    def data_out(self) -> List[str]:
        """List of produced data output types."""
        pass

    @abstractmethod
    async def process(self, task: Task, context: Dict[str, Any]) -> Communication:
        """
        Process a given task using the provided context.
        Returns a Communication object containing the result or next step.
        """
        pass
