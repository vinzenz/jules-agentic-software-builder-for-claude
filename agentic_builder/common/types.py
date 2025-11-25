from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    # Universal Agents
    PM = "PM"
    ARCHITECT = "ARCHITECT"
    UIUX_GUI = "UIUX_GUI"  # UI/UX for graphical interfaces (Web, Mobile, Desktop)
    UIUX_CLI = "UIUX_CLI"  # UX for command-line interfaces
    TEST = "TEST"
    CQR = "CQR"
    SR = "SR"
    DOE = "DOE"

    # UI Layer Agents
    TL_UI_WEB = "TL_UI_WEB"
    DEV_UI_WEB = "DEV_UI_WEB"
    TL_UI_MOBILE = "TL_UI_MOBILE"
    DEV_UI_MOBILE = "DEV_UI_MOBILE"
    TL_UI_DESKTOP = "TL_UI_DESKTOP"
    DEV_UI_DESKTOP = "DEV_UI_DESKTOP"
    TL_UI_CLI = "TL_UI_CLI"
    DEV_UI_CLI = "DEV_UI_CLI"

    # Core Layer Agents
    TL_CORE_API = "TL_CORE_API"
    DEV_CORE_API = "DEV_CORE_API"
    TL_CORE_SYSTEMS = "TL_CORE_SYSTEMS"
    DEV_CORE_SYSTEMS = "DEV_CORE_SYSTEMS"
    TL_CORE_LIBRARY = "TL_CORE_LIBRARY"
    DEV_CORE_LIBRARY = "DEV_CORE_LIBRARY"

    # Platform Layer Agents
    DEV_PLATFORM_IOS = "DEV_PLATFORM_IOS"
    DEV_PLATFORM_ANDROID = "DEV_PLATFORM_ANDROID"
    DEV_PLATFORM_WINDOWS = "DEV_PLATFORM_WINDOWS"
    DEV_PLATFORM_LINUX = "DEV_PLATFORM_LINUX"
    DEV_PLATFORM_MACOS = "DEV_PLATFORM_MACOS"
    DEV_PLATFORM_EMBEDDED = "DEV_PLATFORM_EMBEDDED"

    # Integration Layer Agents
    DEV_INTEGRATION_DATABASE = "DEV_INTEGRATION_DATABASE"
    DEV_INTEGRATION_API = "DEV_INTEGRATION_API"
    DEV_INTEGRATION_NETWORK = "DEV_INTEGRATION_NETWORK"
    DEV_INTEGRATION_HARDWARE = "DEV_INTEGRATION_HARDWARE"

    # Content Layer Agents
    TL_CONTENT = "TL_CONTENT"
    DEV_CONTENT = "DEV_CONTENT"

    # Graphics Layer Agents
    TL_GRAPHICS = "TL_GRAPHICS"
    DEV_GRAPHICS = "DEV_GRAPHICS"

    # Legacy aliases (backward compatibility)
    UIUX = "UIUX"  # Alias for UIUX_GUI (backward compatibility)
    TL_FRONTEND = "TL_FRONTEND"  # Alias for TL_UI_WEB
    DEV_FRONTEND = "DEV_FRONTEND"  # Alias for DEV_UI_WEB
    TL_BACKEND = "TL_BACKEND"  # Alias for TL_CORE_API
    DEV_BACKEND = "DEV_BACKEND"  # Alias for DEV_CORE_API


# Mapping of legacy agent types to new types
AGENT_TYPE_ALIASES = {
    AgentType.UIUX: AgentType.UIUX_GUI,
    AgentType.TL_FRONTEND: AgentType.TL_UI_WEB,
    AgentType.DEV_FRONTEND: AgentType.DEV_UI_WEB,
    AgentType.TL_BACKEND: AgentType.TL_CORE_API,
    AgentType.DEV_BACKEND: AgentType.DEV_CORE_API,
}


def resolve_agent_type(agent_type: AgentType) -> AgentType:
    """Resolve legacy agent types to their new equivalents."""
    return AGENT_TYPE_ALIASES.get(agent_type, agent_type)


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


class ScopeLevel(str, Enum):
    """Project scope level for feature inclusion."""

    MVP = "mvp"  # Minimal viable product (default PM behavior)
    STANDARD = "standard"  # Include common features (auth, basic testing)
    COMPREHENSIVE = "comprehensive"  # All features, full testing, docs, etc.


class OrchestratorType(str, Enum):
    """Available orchestrator engines."""

    ADAPTIVE = "adaptive"  # Discovery-driven, spawns only needed agents
    PARALLEL = "parallel"  # Async parallel execution
    SEQUENTIAL = "sequential"  # Original sequential execution


class WorkflowConstraints(BaseModel):
    """
    Constraints passed to orchestrator to control workflow behavior.

    Used to override default PM behavior (e.g., MVP tendency) and
    configure orchestration options.
    """

    scope: ScopeLevel = ScopeLevel.MVP
    full_feature: bool = False  # Shorthand for scope=comprehensive
    interactive: bool = True  # Enable/disable user prompts
    explicit_includes: List[str] = Field(default_factory=list)  # Features to include
    explicit_excludes: List[str] = Field(default_factory=list)  # Features to skip

    def effective_scope(self) -> ScopeLevel:
        """Return effective scope, considering full_feature flag."""
        if self.full_feature:
            return ScopeLevel.COMPREHENSIVE
        return self.scope

    def to_manifest_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for manifest storage."""
        return {
            "scope": self.effective_scope().value,
            "full_feature": self.full_feature,
            "interactive": self.interactive,
            "explicit_includes": self.explicit_includes,
            "explicit_excludes": self.explicit_excludes,
        }


class Artifact(BaseModel):
    name: str
    type: str  # file, diff, plan, etc.
    path: Optional[str] = None
    content: Optional[str] = None  # Content is optional - agents write files directly to disk
    action: Optional[str] = None  # "created" or "modified"


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
    # Store agent output for passing context to dependent agents
    output_summary: Optional[str] = None
    output_next_steps: List[str] = Field(default_factory=list)
    output_warnings: List[str] = Field(default_factory=list)


class SessionData(BaseModel):
    id: str
    workflow_name: str
    status: WorkflowStatus
    idea: Optional[str] = None  # Project idea/description passed at workflow start
    output_dir: Optional[str] = None  # Project root directory for all file operations
    start_time: datetime = Field(default_factory=datetime.now)
    current_stage: int = 0
    completed_tasks: List[str] = Field(default_factory=list)
    checkpoints: Dict[str, Any] = Field(default_factory=dict)
    total_tokens: int = 0
