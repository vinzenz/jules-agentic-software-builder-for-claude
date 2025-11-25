from agentic_builder.agents.configs import AGENT_CONFIGS, get_agent_config
from agentic_builder.agents.response_parser import ResponseParser
from agentic_builder.common.types import AgentType, ModelTier


def test_agent_configs_completeness():
    # Check all 11 agents exist
    assert len(AGENT_CONFIGS) >= 11
    types = [c.type for c in AGENT_CONFIGS]
    assert AgentType.PM in types
    assert AgentType.DEV_BACKEND in types


def test_model_selection():
    # Verify tiers as per spec
    # opus: PM, ARCHITECT, UIUX_GUI, SR, TL_CONTENT, TL_GRAPHICS
    assert get_agent_config(AgentType.PM).model_tier == ModelTier.OPUS
    assert get_agent_config(AgentType.ARCHITECT).model_tier == ModelTier.OPUS
    assert get_agent_config(AgentType.SR).model_tier == ModelTier.OPUS
    assert get_agent_config(AgentType.UIUX_GUI).model_tier == ModelTier.OPUS
    assert get_agent_config(AgentType.TL_GRAPHICS).model_tier == ModelTier.OPUS

    # UIUX is an alias for UIUX_GUI, so it should also be OPUS
    assert get_agent_config(AgentType.UIUX).model_tier == ModelTier.OPUS

    # sonnet: DEV_, TL_, TEST, CQR, DOE, UIUX_CLI
    assert get_agent_config(AgentType.DEV_FRONTEND).model_tier == ModelTier.SONNET
    assert get_agent_config(AgentType.TL_FRONTEND).model_tier == ModelTier.SONNET
    assert get_agent_config(AgentType.TEST).model_tier == ModelTier.SONNET
    assert get_agent_config(AgentType.CQR).model_tier == ModelTier.SONNET
    assert get_agent_config(AgentType.DOE).model_tier == ModelTier.SONNET
    assert get_agent_config(AgentType.UIUX_CLI).model_tier == ModelTier.SONNET


def test_response_parser_success():
    raw_response = """
    Thinking process...
    <summary>Completed the task successfully.</summary>
    <next_steps>
    - Step 1
    - Step 2
    </next_steps>
    <artifact name="test.py" type="file">
    print("hello")
    </artifact>
    """

    parsed = ResponseParser.parse(raw_response)
    assert parsed.success
    assert parsed.summary == "Completed the task successfully."
    assert len(parsed.next_steps) == 2
    assert len(parsed.artifacts) == 1
    assert parsed.artifacts[0].name == "test.py"
    assert parsed.artifacts[0].content.strip() == 'print("hello")'


def test_response_parser_failure():
    # Parser should default to success=True unless specific failure marker or empty?
    # Or maybe we assume success if we parse correctly.
    # Let's say if no summary/artifacts found, maybe valid but empty.

    # Let's test malformed
    raw = "Just some text"
    parsed = ResponseParser.parse(raw)
    # Depending on implementation, might fallback to treating whole text as summary
    assert parsed.summary == "Just some text"
