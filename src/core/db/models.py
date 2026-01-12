from datetime import datetime, timezone
from typing import List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncAttrs

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Goal(Base):
    __tablename__ = "goals"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    tasks: Mapped[List["Task"]] = relationship(back_populates="goal", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    goal_id: Mapped[UUID] = mapped_column(ForeignKey("goals.id"))
    parent_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    
    title: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(50)) # e.g. GENERATION, REVIEW
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    assigned_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) # Agent ID
    
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default={})
    result: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    goal: Mapped["Goal"] = relationship(back_populates="tasks")
    
    # Adjacency List Relationship
    parent: Mapped[Optional["Task"]] = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks: Mapped[List["Task"]] = relationship("Task", back_populates="parent", cascade="all, delete-orphan")
    
    artifacts: Mapped[List["Artifact"]] = relationship(back_populates="task", cascade="all, delete-orphan")

class Artifact(Base):
    __tablename__ = "artifacts"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id"))
    
    name: Mapped[str] = mapped_column(String(255))
    path: Mapped[str] = mapped_column(String(1024)) # Absolute path
    media_type: Mapped[str] = mapped_column(String(100), default="text/markdown")
    
    current_version_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("artifact_versions.id"), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    task: Mapped["Task"] = relationship(back_populates="artifacts")
    versions: Mapped[List["ArtifactVersion"]] = relationship(primaryjoin="Artifact.id==ArtifactVersion.artifact_id", back_populates="artifact")

class ArtifactVersion(Base):
    __tablename__ = "artifact_versions"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    artifact_id: Mapped[UUID] = mapped_column(ForeignKey("artifacts.id"))
    
    version_number: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text) # For text files. Binary refs likely external.
    created_by_agent: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    artifact: Mapped["Artifact"] = relationship(back_populates="versions", foreign_keys=[artifact_id])

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    actor_id: Mapped[str] = mapped_column(String(50))
    action_type: Mapped[str] = mapped_column(String(100))
    
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[UUID] = mapped_column()
    
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default={})
