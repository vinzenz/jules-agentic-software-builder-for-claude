from typing import List

from pydantic import BaseModel

from agentic_builder.common.types import AgentType, ModelTier, resolve_agent_type


class AgentConfig(BaseModel):
    type: AgentType
    model_tier: ModelTier
    dependencies: List[AgentType]
    layer: str = "universal"  # universal, ui, core, platform, integration


# Agent Configuration Map
# Organized by layer for clarity
#
# Dependency Rules:
# - PM has no dependencies (entry point)
# - ARCHITECT depends on PM
# - UIUX_GUI depends on PM (for graphical interfaces: Web, Mobile, Desktop)
# - UIUX_CLI depends on PM (for command-line interface usability)
# - TL_UI_WEB/MOBILE/DESKTOP agents depend on ARCHITECT and UIUX_GUI
# - TL_UI_CLI agents depend on ARCHITECT and UIUX_CLI
# - DEV_* agents depend on their corresponding TL_*
# - Platform agents depend on ARCHITECT
# - Integration agents depend on ARCHITECT
# - TEST, CQR, SR, DOE dependencies are set dynamically based on workflow

AGENT_CONFIGS_MAP = {
    # ========================================
    # UNIVERSAL AGENTS
    # ========================================
    AgentType.PM: AgentConfig(
        type=AgentType.PM,
        model_tier=ModelTier.OPUS,
        dependencies=[],
        layer="universal",
    ),
    AgentType.ARCHITECT: AgentConfig(
        type=AgentType.ARCHITECT,
        model_tier=ModelTier.OPUS,
        dependencies=[AgentType.PM],
        layer="universal",
    ),
    AgentType.UIUX_GUI: AgentConfig(
        type=AgentType.UIUX_GUI,
        model_tier=ModelTier.OPUS,
        dependencies=[AgentType.PM],
        layer="universal",
    ),
    AgentType.UIUX_CLI: AgentConfig(
        type=AgentType.UIUX_CLI,
        model_tier=ModelTier.SONNET,  # CLI UX is more constrained than GUI
        dependencies=[AgentType.PM],
        layer="universal",
    ),
    AgentType.TEST: AgentConfig(
        type=AgentType.TEST,
        model_tier=ModelTier.SONNET,
        dependencies=[],  # Dependencies set dynamically based on workflow
        layer="universal",
    ),
    AgentType.CQR: AgentConfig(
        type=AgentType.CQR,
        model_tier=ModelTier.SONNET,
        dependencies=[],  # Dependencies set dynamically based on workflow
        layer="universal",
    ),
    AgentType.SR: AgentConfig(
        type=AgentType.SR,
        model_tier=ModelTier.OPUS,
        dependencies=[],  # Dependencies set dynamically based on workflow
        layer="universal",
    ),
    AgentType.DOE: AgentConfig(
        type=AgentType.DOE,
        model_tier=ModelTier.SONNET,
        dependencies=[],  # Dependencies set dynamically based on workflow
        layer="universal",
    ),

    # ========================================
    # UI LAYER AGENTS
    # ========================================
    # Web UI
    AgentType.TL_UI_WEB: AgentConfig(
        type=AgentType.TL_UI_WEB,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_GUI],
        layer="ui",
    ),
    AgentType.DEV_UI_WEB: AgentConfig(
        type=AgentType.DEV_UI_WEB,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_UI_WEB],
        layer="ui",
    ),
    # Mobile UI
    AgentType.TL_UI_MOBILE: AgentConfig(
        type=AgentType.TL_UI_MOBILE,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_GUI],
        layer="ui",
    ),
    AgentType.DEV_UI_MOBILE: AgentConfig(
        type=AgentType.DEV_UI_MOBILE,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_UI_MOBILE],
        layer="ui",
    ),
    # Desktop UI
    AgentType.TL_UI_DESKTOP: AgentConfig(
        type=AgentType.TL_UI_DESKTOP,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_GUI],
        layer="ui",
    ),
    AgentType.DEV_UI_DESKTOP: AgentConfig(
        type=AgentType.DEV_UI_DESKTOP,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_UI_DESKTOP],
        layer="ui",
    ),
    # CLI UI
    AgentType.TL_UI_CLI: AgentConfig(
        type=AgentType.TL_UI_CLI,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_CLI],
        layer="ui",
    ),
    AgentType.DEV_UI_CLI: AgentConfig(
        type=AgentType.DEV_UI_CLI,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_UI_CLI],
        layer="ui",
    ),

    # ========================================
    # CORE LAYER AGENTS
    # ========================================
    # API/Services
    AgentType.TL_CORE_API: AgentConfig(
        type=AgentType.TL_CORE_API,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="core",
    ),
    AgentType.DEV_CORE_API: AgentConfig(
        type=AgentType.DEV_CORE_API,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_CORE_API],
        layer="core",
    ),
    # Systems Programming
    AgentType.TL_CORE_SYSTEMS: AgentConfig(
        type=AgentType.TL_CORE_SYSTEMS,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="core",
    ),
    AgentType.DEV_CORE_SYSTEMS: AgentConfig(
        type=AgentType.DEV_CORE_SYSTEMS,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_CORE_SYSTEMS],
        layer="core",
    ),
    # Library Development
    AgentType.TL_CORE_LIBRARY: AgentConfig(
        type=AgentType.TL_CORE_LIBRARY,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="core",
    ),
    AgentType.DEV_CORE_LIBRARY: AgentConfig(
        type=AgentType.DEV_CORE_LIBRARY,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_CORE_LIBRARY],
        layer="core",
    ),

    # ========================================
    # PLATFORM LAYER AGENTS
    # ========================================
    AgentType.DEV_PLATFORM_IOS: AgentConfig(
        type=AgentType.DEV_PLATFORM_IOS,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_ANDROID: AgentConfig(
        type=AgentType.DEV_PLATFORM_ANDROID,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_WINDOWS: AgentConfig(
        type=AgentType.DEV_PLATFORM_WINDOWS,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_LINUX: AgentConfig(
        type=AgentType.DEV_PLATFORM_LINUX,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_MACOS: AgentConfig(
        type=AgentType.DEV_PLATFORM_MACOS,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_EMBEDDED: AgentConfig(
        type=AgentType.DEV_PLATFORM_EMBEDDED,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),

    # ========================================
    # INTEGRATION LAYER AGENTS
    # ========================================
    AgentType.DEV_INTEGRATION_DATABASE: AgentConfig(
        type=AgentType.DEV_INTEGRATION_DATABASE,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),
    AgentType.DEV_INTEGRATION_API: AgentConfig(
        type=AgentType.DEV_INTEGRATION_API,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),
    AgentType.DEV_INTEGRATION_NETWORK: AgentConfig(
        type=AgentType.DEV_INTEGRATION_NETWORK,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),
    AgentType.DEV_INTEGRATION_HARDWARE: AgentConfig(
        type=AgentType.DEV_INTEGRATION_HARDWARE,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),

    # ========================================
    # CONTENT LAYER AGENTS
    # ========================================
    AgentType.TL_CONTENT: AgentConfig(
        type=AgentType.TL_CONTENT,
        model_tier=ModelTier.OPUS,
        dependencies=[AgentType.PM],  # Content strategy comes from PM requirements
        layer="content",
    ),
    AgentType.DEV_CONTENT: AgentConfig(
        type=AgentType.DEV_CONTENT,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_CONTENT],
        layer="content",
    ),

    # ========================================
    # GRAPHICS LAYER AGENTS
    # ========================================
    AgentType.TL_GRAPHICS: AgentConfig(
        type=AgentType.TL_GRAPHICS,
        model_tier=ModelTier.OPUS,
        dependencies=[AgentType.PM],  # Brand/visual strategy comes from PM requirements
        layer="graphics",
    ),
    AgentType.DEV_GRAPHICS: AgentConfig(
        type=AgentType.DEV_GRAPHICS,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_GRAPHICS],
        layer="graphics",
    ),

    # ========================================
    # LEGACY ALIASES (backward compatibility)
    # ========================================
    AgentType.UIUX: AgentConfig(
        type=AgentType.UIUX,
        model_tier=ModelTier.OPUS,
        dependencies=[AgentType.PM],
        layer="universal",
    ),
    AgentType.TL_FRONTEND: AgentConfig(
        type=AgentType.TL_FRONTEND,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_GUI],
        layer="ui",
    ),
    AgentType.DEV_FRONTEND: AgentConfig(
        type=AgentType.DEV_FRONTEND,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_FRONTEND],
        layer="ui",
    ),
    AgentType.TL_BACKEND: AgentConfig(
        type=AgentType.TL_BACKEND,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT],
        layer="core",
    ),
    AgentType.DEV_BACKEND: AgentConfig(
        type=AgentType.DEV_BACKEND,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.TL_BACKEND],
        layer="core",
    ),
}

AGENT_CONFIGS = list(AGENT_CONFIGS_MAP.values())


def get_agent_config(agent_type: AgentType) -> AgentConfig:
    """Get configuration for an agent type, resolving aliases if needed.

    Raises:
        ValueError: If no configuration exists for the agent type.
    """
    resolved_type = resolve_agent_type(agent_type)
    config = AGENT_CONFIGS_MAP.get(resolved_type) or AGENT_CONFIGS_MAP.get(agent_type)
    if config is None:
        raise ValueError(
            f"No configuration found for agent type '{agent_type.value}'. "
            f"Please add a config entry in AGENT_CONFIGS_MAP."
        )
    return config


def get_agents_by_layer(layer: str) -> List[AgentConfig]:
    """Get all agents belonging to a specific layer."""
    return [config for config in AGENT_CONFIGS if config.layer == layer]


def get_agent_prompt(agent_type: AgentType) -> str:
    """Load the prompt for an agent from its XML file."""
    from pathlib import Path

    prompt = ""
    # Prepend common schema instructions
    schema_path = Path("prompts/common_schema.xml")
    if schema_path.exists():
        prompt += schema_path.read_text() + "\n\n"

    # Try resolved type first, then original type
    resolved_type = resolve_agent_type(agent_type)
    path = Path(f"prompts/agents/{resolved_type.value}.xml")
    if not path.exists():
        path = Path(f"prompts/agents/{agent_type.value}.xml")

    if path.exists():
        prompt += path.read_text()
        return prompt

    return prompt + f"You are {agent_type.value}."
