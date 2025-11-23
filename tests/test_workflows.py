from agentic_builder.common.types import AgentType
from agentic_builder.orchestration.workflows import WorkflowMapper, WorkflowType


def test_workflow_mapper_full_app():
    order = WorkflowMapper.get_execution_order(WorkflowType.FULL_APP_GENERATION)

    # Verify PM is first (or early)
    assert order[0] == AgentType.PM
    # Verify ARCHITECT comes after PM
    assert order.index(AgentType.ARCHITECT) > order.index(AgentType.PM)
    # Verify DEV comes after TL
    assert order.index(AgentType.DEV_FRONTEND) > order.index(AgentType.TL_FRONTEND)

    # Verify all agents are present
    assert len(order) == 11


def test_workflow_mapper_code_review():
    order = WorkflowMapper.get_execution_order(WorkflowType.CODE_REVIEW)
    assert len(order) == 1
    assert order[0] == AgentType.CQR


def test_workflow_mapper_feature_addition():
    order = WorkflowMapper.get_execution_order(WorkflowType.FEATURE_ADDITION)
    # Should include PM, ARCH, etc.
    assert AgentType.PM in order
    assert AgentType.DEV_BACKEND in order
    # Verify sorting
    assert order.index(AgentType.DEV_BACKEND) > order.index(AgentType.TL_BACKEND)
