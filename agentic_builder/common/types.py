from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    PM = "PM"
    ARCHITECT = "ARCHITECT"
    UIUX = "UIUX"
    TL_FRONTEND = "TL_FRONTEND"
    TL_BACKEND = "TL_BACKEND"
    DEV_FRONTEND = "DEV_FRONTEND"
    DEV_BACKEND = "DEV_BACKEND"
    TEST = "TEST"
    CQR = "CQR"
    SR = "SR"
    DOE = "DOE"


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    SPAWNING = "SPAWNING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ModelTier(str, Enum):
    OPUS = "opus"
    SONNET = "sonnet"
    HAIKU = "haiku"


class Artifact(BaseModel):
    name: str
    type: str  # file, diff, plan, etc.
    path: Optional[str] = None
    content: str


class AgentOutput(BaseModel):
    success: bool
    summary: str
    artifacts: List[Artifact] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    next_steps: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class Task(BaseModel):
    id: str
    description: str
    agent_type: AgentType
    status: str = "pending"
    dependencies: List[str] = Field(default_factory=list)  # Task IDs
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    context_files: List[str] = Field(default_factory=list)


class SessionData(BaseModel):
    id: str
    workflow_name: str
    status: WorkflowStatus
    start_time: datetime = Field(default_factory=datetime.now)
    current_stage: int = 0
    completed_tasks: List[str] = Field(default_factory=list)
    checkpoints: Dict[str, Any] = Field(default_factory=dict)
    total_tokens: int = 0
