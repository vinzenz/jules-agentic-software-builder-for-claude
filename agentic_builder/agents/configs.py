from typing import List

from pydantic import BaseModel

from agentic_builder.common.types import AgentType, ModelTier


class AgentConfig(BaseModel):
    type: AgentType
    model_tier: ModelTier
    dependencies: List[AgentType]


# Dependency Map:
# PM (no deps)
# ARCHITECT (PM)
# TL_FRONTEND (ARCHITECT, UIUX)
# DEV_FRONTEND (TL_FRONTEND) <-- spec said DEV depends on TL? Check: "DEV_FRONTEND -> UIUX (PM)"
# Wait spec said: "TL_FRONTEND (ARCHITECT,UIUX) -> DEV_FRONTEND"
# "UIUX (PM)"
# "TL_BACKEND (ARCHITECT) -> DEV_BACKEND"
# "TEST, CQR, SR, DOE" (Usually depend on Devs)

# Re-reading spec:
# PM (no deps)
# ARCHITECT (PM)
# TL_FRONTEND (ARCHITECT,UIUX)
# DEV_FRONTEND -> Implied depends on TL_FRONTEND? Spec diagram says "DEV_FRONTEND" follows TL.
# UIUX (PM)
# TL_BACKEND (ARCHITECT)
# DEV_BACKEND -> Implied depends on TL_BACKEND?
# TEST, CQR, SR, DOE -> likely depend on DEVs.

# Let's formalize a sensible graph based on "12 agent types with dependencies: PM (no deps) -> ARCHITECT (PM)
# -> TL_FRONTEND (ARCHITECT,UIUX) -> DEV_FRONTEND -> UIUX (PM) -> TL_BACKEND (ARCHITECT) -> DEV_BACKEND
# -> TEST, CQR, SR, DOE"
# This linear arrow notation is slightly confusing.
# Interpretation:
# PM: []
# ARCHITECT: [PM]
# UIUX: [PM]
# TL_FRONTEND: [ARCHITECT, UIUX]
# DEV_FRONTEND: [TL_FRONTEND]
# TL_BACKEND: [ARCHITECT]
# DEV_BACKEND: [TL_BACKEND]
# TEST: [DEV_FRONTEND, DEV_BACKEND]
# CQR: [DEV_FRONTEND, DEV_BACKEND]
# SR: [DEV_FRONTEND, DEV_BACKEND]
# DOE: [DEV_FRONTEND, DEV_BACKEND]

AGENT_CONFIGS_MAP = {
    AgentType.PM: AgentConfig(type=AgentType.PM, model_tier=ModelTier.OPUS, dependencies=[]),
    AgentType.ARCHITECT: AgentConfig(type=AgentType.ARCHITECT, model_tier=ModelTier.OPUS, dependencies=[AgentType.PM]),
    AgentType.UIUX: AgentConfig(type=AgentType.UIUX, model_tier=ModelTier.OPUS, dependencies=[AgentType.PM]),
    AgentType.TL_FRONTEND: AgentConfig(
        type=AgentType.TL_FRONTEND, model_tier=ModelTier.SONNET, dependencies=[AgentType.ARCHITECT, AgentType.UIUX]
    ),
    AgentType.DEV_FRONTEND: AgentConfig(
        type=AgentType.DEV_FRONTEND, model_tier=ModelTier.SONNET, dependencies=[AgentType.TL_FRONTEND]
    ),
    AgentType.TL_BACKEND: AgentConfig(
        type=AgentType.TL_BACKEND, model_tier=ModelTier.SONNET, dependencies=[AgentType.ARCHITECT]
    ),
    AgentType.DEV_BACKEND: AgentConfig(
        type=AgentType.DEV_BACKEND, model_tier=ModelTier.SONNET, dependencies=[AgentType.TL_BACKEND]
    ),
    # Review/QA agents
    AgentType.TEST: AgentConfig(
        type=AgentType.TEST, model_tier=ModelTier.SONNET, dependencies=[AgentType.DEV_FRONTEND, AgentType.DEV_BACKEND]
    ),
    AgentType.CQR: AgentConfig(
        type=AgentType.CQR, model_tier=ModelTier.SONNET, dependencies=[AgentType.DEV_FRONTEND, AgentType.DEV_BACKEND]
    ),
    AgentType.SR: AgentConfig(
        type=AgentType.SR, model_tier=ModelTier.OPUS, dependencies=[AgentType.DEV_FRONTEND, AgentType.DEV_BACKEND]
    ),
    AgentType.DOE: AgentConfig(
        type=AgentType.DOE, model_tier=ModelTier.HAIKU, dependencies=[AgentType.DEV_FRONTEND, AgentType.DEV_BACKEND]
    ),
}

AGENT_CONFIGS = list(AGENT_CONFIGS_MAP.values())


def get_agent_config(agent_type: AgentType) -> AgentConfig:
    return AGENT_CONFIGS_MAP[agent_type]


def get_agent_prompt(agent_type: AgentType) -> str:
    from pathlib import Path

    prompt = ""
    # Prepend common schema instructions
    schema_path = Path("prompts/common_schema.xml")
    if schema_path.exists():
        prompt += schema_path.read_text() + "\n\n"

    path = Path(f"prompts/agents/{agent_type.value}.xml")
    if path.exists():
        prompt += path.read_text()
        return prompt

    return prompt + f"You are {agent_type.value}."
