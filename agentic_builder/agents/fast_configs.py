"""
Fast Agent Configurations - Optimized for Speed

This module provides an alternative configuration that aggressively downgrades
model tiers for faster execution times.

Model Tier Strategy:
- Opus (2): PM (critical planning), SR (security-critical)
- Sonnet (10): Design/architecture roles that need reasoning
- Haiku (26): Implementation roles with well-defined specifications

Expected Speed Improvement:
    Current: (6 × 60s) + (32 × 30s) = 22 min model time
    Optimized: (2 × 60s) + (10 × 30s) + (26 × 6s) = 8.1 min model time
    Speedup: 2.7x from model downgrades alone

Usage:
    from agentic_builder.agents.fast_configs import FAST_AGENT_CONFIGS_MAP
"""

from typing import List

from pydantic import BaseModel

from agentic_builder.common.types import AgentType, ModelTier, resolve_agent_type


class AgentConfig(BaseModel):
    type: AgentType
    model_tier: ModelTier
    dependencies: List[AgentType]
    layer: str = "universal"


# ============================================================================
# FAST AGENT CONFIGURATIONS - Optimized for Speed
# ============================================================================
#
# Tier Distribution:
# - OPUS (2 agents): PM, SR
# - SONNET (10 agents): ARCHITECT, UIUX_*, TL_*, TEST
# - HAIKU (26 agents): All DEV_*, CQR, DOE, Content, Graphics
#

FAST_AGENT_CONFIGS_MAP = {
    # ========================================
    # OPUS TIER - Critical Reasoning Only
    # ========================================
    AgentType.PM: AgentConfig(
        type=AgentType.PM,
        model_tier=ModelTier.OPUS,  # Keep: Project planning is critical
        dependencies=[],
        layer="universal",
    ),
    AgentType.SR: AgentConfig(
        type=AgentType.SR,
        model_tier=ModelTier.OPUS,  # Keep: Security requires deep analysis
        dependencies=[],
        layer="universal",
    ),

    # ========================================
    # SONNET TIER - Design & Architecture
    # ========================================
    AgentType.ARCHITECT: AgentConfig(
        type=AgentType.ARCHITECT,
        model_tier=ModelTier.SONNET,  # Downgraded: Still needs reasoning
        dependencies=[AgentType.PM],
        layer="universal",
    ),
    AgentType.UIUX_GUI: AgentConfig(
        type=AgentType.UIUX_GUI,
        model_tier=ModelTier.SONNET,  # Downgraded: UI design needs reasoning
        dependencies=[AgentType.PM],
        layer="universal",
    ),
    AgentType.UIUX_CLI: AgentConfig(
        type=AgentType.UIUX_CLI,
        model_tier=ModelTier.SONNET,  # Keep: CLI UX needs thought
        dependencies=[AgentType.PM],
        layer="universal",
    ),
    AgentType.TEST: AgentConfig(
        type=AgentType.TEST,
        model_tier=ModelTier.SONNET,  # Keep: Test strategy needs reasoning
        dependencies=[],
        layer="universal",
    ),
    AgentType.TL_UI_WEB: AgentConfig(
        type=AgentType.TL_UI_WEB,
        model_tier=ModelTier.SONNET,  # Keep: Tech decisions
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_GUI],
        layer="ui",
    ),
    AgentType.TL_UI_MOBILE: AgentConfig(
        type=AgentType.TL_UI_MOBILE,
        model_tier=ModelTier.SONNET,
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_GUI],
        layer="ui",
    ),
    AgentType.TL_CORE_API: AgentConfig(
        type=AgentType.TL_CORE_API,
        model_tier=ModelTier.SONNET,  # Keep: API design decisions
        dependencies=[AgentType.ARCHITECT],
        layer="core",
    ),
    AgentType.TL_CORE_SYSTEMS: AgentConfig(
        type=AgentType.TL_CORE_SYSTEMS,
        model_tier=ModelTier.SONNET,  # Keep: Systems design
        dependencies=[AgentType.ARCHITECT],
        layer="core",
    ),

    # ========================================
    # HAIKU TIER - Fast Implementation
    # ========================================

    # Quality & Ops (downgraded)
    AgentType.CQR: AgentConfig(
        type=AgentType.CQR,
        model_tier=ModelTier.HAIKU,  # Downgraded: Pattern matching
        dependencies=[],
        layer="universal",
    ),
    AgentType.DOE: AgentConfig(
        type=AgentType.DOE,
        model_tier=ModelTier.HAIKU,  # Downgraded: Template-based
        dependencies=[],
        layer="universal",
    ),

    # UI Layer DEV agents (all Haiku)
    AgentType.DEV_UI_WEB: AgentConfig(
        type=AgentType.DEV_UI_WEB,
        model_tier=ModelTier.HAIKU,  # Downgraded: Implementation
        dependencies=[AgentType.TL_UI_WEB],
        layer="ui",
    ),
    AgentType.DEV_UI_MOBILE: AgentConfig(
        type=AgentType.DEV_UI_MOBILE,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_UI_MOBILE],
        layer="ui",
    ),
    AgentType.TL_UI_DESKTOP: AgentConfig(
        type=AgentType.TL_UI_DESKTOP,
        model_tier=ModelTier.HAIKU,  # Downgraded: Less common
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_GUI],
        layer="ui",
    ),
    AgentType.DEV_UI_DESKTOP: AgentConfig(
        type=AgentType.DEV_UI_DESKTOP,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_UI_DESKTOP],
        layer="ui",
    ),
    AgentType.TL_UI_CLI: AgentConfig(
        type=AgentType.TL_UI_CLI,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT, AgentType.UIUX_CLI],
        layer="ui",
    ),
    AgentType.DEV_UI_CLI: AgentConfig(
        type=AgentType.DEV_UI_CLI,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_UI_CLI],
        layer="ui",
    ),

    # Core Layer DEV agents (all Haiku)
    AgentType.DEV_CORE_API: AgentConfig(
        type=AgentType.DEV_CORE_API,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_CORE_API],
        layer="core",
    ),
    AgentType.DEV_CORE_SYSTEMS: AgentConfig(
        type=AgentType.DEV_CORE_SYSTEMS,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_CORE_SYSTEMS],
        layer="core",
    ),
    AgentType.TL_CORE_LIBRARY: AgentConfig(
        type=AgentType.TL_CORE_LIBRARY,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="core",
    ),
    AgentType.DEV_CORE_LIBRARY: AgentConfig(
        type=AgentType.DEV_CORE_LIBRARY,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_CORE_LIBRARY],
        layer="core",
    ),

    # Platform Layer (all Haiku - specialized but template-based)
    AgentType.DEV_PLATFORM_IOS: AgentConfig(
        type=AgentType.DEV_PLATFORM_IOS,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_ANDROID: AgentConfig(
        type=AgentType.DEV_PLATFORM_ANDROID,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_WINDOWS: AgentConfig(
        type=AgentType.DEV_PLATFORM_WINDOWS,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_LINUX: AgentConfig(
        type=AgentType.DEV_PLATFORM_LINUX,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_MACOS: AgentConfig(
        type=AgentType.DEV_PLATFORM_MACOS,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),
    AgentType.DEV_PLATFORM_EMBEDDED: AgentConfig(
        type=AgentType.DEV_PLATFORM_EMBEDDED,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="platform",
    ),

    # Integration Layer (all Haiku)
    AgentType.DEV_INTEGRATION_DATABASE: AgentConfig(
        type=AgentType.DEV_INTEGRATION_DATABASE,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),
    AgentType.DEV_INTEGRATION_API: AgentConfig(
        type=AgentType.DEV_INTEGRATION_API,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),
    AgentType.DEV_INTEGRATION_NETWORK: AgentConfig(
        type=AgentType.DEV_INTEGRATION_NETWORK,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),
    AgentType.DEV_INTEGRATION_HARDWARE: AgentConfig(
        type=AgentType.DEV_INTEGRATION_HARDWARE,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.ARCHITECT],
        layer="integration",
    ),

    # Content Layer (all Haiku - text generation is well-specified)
    AgentType.TL_CONTENT: AgentConfig(
        type=AgentType.TL_CONTENT,
        model_tier=ModelTier.HAIKU,  # Downgraded from Opus
        dependencies=[AgentType.PM],
        layer="content",
    ),
    AgentType.DEV_CONTENT: AgentConfig(
        type=AgentType.DEV_CONTENT,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_CONTENT],
        layer="content",
    ),

    # Graphics Layer (all Haiku - mostly tool invocation)
    AgentType.TL_GRAPHICS: AgentConfig(
        type=AgentType.TL_GRAPHICS,
        model_tier=ModelTier.HAIKU,  # Downgraded from Opus
        dependencies=[AgentType.PM],
        layer="graphics",
    ),
    AgentType.DEV_GRAPHICS: AgentConfig(
        type=AgentType.DEV_GRAPHICS,
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_GRAPHICS],
        layer="graphics",
    ),

    # ========================================
    # LEGACY ALIASES
    # ========================================
    AgentType.UIUX: AgentConfig(
        type=AgentType.UIUX,
        model_tier=ModelTier.SONNET,
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
        model_tier=ModelTier.HAIKU,
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
        model_tier=ModelTier.HAIKU,
        dependencies=[AgentType.TL_BACKEND],
        layer="core",
    ),
}

FAST_AGENT_CONFIGS = list(FAST_AGENT_CONFIGS_MAP.values())


def get_fast_agent_config(agent_type: AgentType) -> AgentConfig:
    """Get fast configuration for an agent type."""
    resolved_type = resolve_agent_type(agent_type)
    config = FAST_AGENT_CONFIGS_MAP.get(resolved_type) or FAST_AGENT_CONFIGS_MAP.get(agent_type)
    if config is None:
        raise ValueError(f"No fast config for agent type '{agent_type.value}'")
    return config


def get_tier_distribution() -> dict:
    """Get count of agents per model tier."""
    from collections import Counter
    tiers = Counter(c.model_tier.value for c in FAST_AGENT_CONFIGS)
    return dict(tiers)


def print_tier_summary():
    """Print summary of model tier distribution."""
    dist = get_tier_distribution()
    print("Fast Config Model Tier Distribution:")
    for tier, count in sorted(dist.items()):
        print(f"  {tier}: {count} agents")

    # Time estimate
    opus_time = dist.get("opus", 0) * 60
    sonnet_time = dist.get("sonnet", 0) * 30
    haiku_time = dist.get("haiku", 0) * 6
    total_time = opus_time + sonnet_time + haiku_time
    print(f"\nEstimated model time: {total_time / 60:.1f} minutes")
