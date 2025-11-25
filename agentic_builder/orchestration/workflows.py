from enum import Enum
from typing import Dict, List

from agentic_builder.agents.configs import get_agent_config
from agentic_builder.common.types import AgentType


class WorkflowType(str, Enum):
    FULL_APP_GENERATION = "FULL_APP_GENERATION"
    FEATURE_ADDITION = "FEATURE_ADDITION"
    BUG_FIX = "BUG_FIX"
    REFACTORING = "REFACTORING"
    TEST_GENERATION = "TEST_GENERATION"
    CODE_REVIEW = "CODE_REVIEW"
    SECURITY_AUDIT = "SECURITY_AUDIT"


# Define which agents participate in each workflow
WORKFLOW_TEMPLATES: Dict[WorkflowType, List[AgentType]] = {
    WorkflowType.FULL_APP_GENERATION: list(AgentType),  # All agents
    WorkflowType.FEATURE_ADDITION: [
        AgentType.PM,
        AgentType.ARCHITECT,
        AgentType.UIUX_GUI,
        AgentType.UIUX_CLI,
        AgentType.TL_FRONTEND,
        AgentType.TL_BACKEND,
        AgentType.DEV_FRONTEND,
        AgentType.DEV_BACKEND,
        AgentType.TEST,
        AgentType.CQR,
        AgentType.SR,
        AgentType.DOE,
    ],
    WorkflowType.BUG_FIX: [
        AgentType.PM,  # To analyze bug report
        AgentType.TL_FRONTEND,
        AgentType.TL_BACKEND,
        AgentType.DEV_FRONTEND,
        AgentType.DEV_BACKEND,
        AgentType.TEST,
    ],
    WorkflowType.REFACTORING: [
        AgentType.ARCHITECT,
        AgentType.TL_FRONTEND,
        AgentType.TL_BACKEND,
        AgentType.DEV_FRONTEND,
        AgentType.DEV_BACKEND,
        AgentType.CQR,
    ],
    WorkflowType.TEST_GENERATION: [AgentType.TEST],
    WorkflowType.CODE_REVIEW: [AgentType.CQR],
    WorkflowType.SECURITY_AUDIT: [AgentType.SR],
}


class WorkflowMapper:
    @staticmethod
    def get_execution_order(workflow_type: str) -> List[AgentType]:
        # Handle string input from CLI
        try:
            w_type = WorkflowType(workflow_type)
        except ValueError:
            # Fallback or default? Or maybe strict.
            # If user types "create-app", mapped to FULL_APP...
            # The CLI might handle aliases. For now assume internal name.
            if workflow_type == "create-app":
                w_type = WorkflowType.FULL_APP_GENERATION
            else:
                w_type = WorkflowType.FULL_APP_GENERATION  # Default? Or raise.

        agents = WORKFLOW_TEMPLATES.get(w_type, [])
        return WorkflowMapper.topological_sort(agents)

    @staticmethod
    def topological_sort(agents: List[AgentType]) -> List[AgentType]:
        """
        Sorts the provided list of agents based on the dependency graph in AGENT_CONFIGS.
        Only considers dependencies that are present in the input list.
        """
        # Build adjacency list for the subset
        # adj: Dict[AgentType, Set[AgentType]] = {a: set() for a in agents}

        # Populate dependencies
        for agent in agents:
            config = get_agent_config(agent)
            for dep in config.dependencies:
                if dep in agents:
                    # dep must come before agent
                    # so dependency edge is dep -> agent
                    # For topo sort, we usually track incoming edges (dependencies)
                    pass

        # Standard Kahn's algorithm or DFS
        # Let's use simple DFS post-order (reverse) or just dependency counting

        # State: 0=unvisited, 1=visiting, 2=visited
        state = {a: 0 for a in agents}
        result = []

        def visit(node):
            if state[node] == 1:
                raise ValueError("Cycle detected in agent dependencies")
            if state[node] == 2:
                return

            state[node] = 1

            # Visit dependencies first
            config = get_agent_config(node)
            for dep in config.dependencies:
                if dep in agents:
                    visit(dep)

            state[node] = 2
            result.append(node)

        for agent in agents:
            if state[agent] == 0:
                visit(agent)

        return result
