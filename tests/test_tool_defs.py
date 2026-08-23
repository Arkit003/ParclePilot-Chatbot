from src.agent.tool_defs import TOOL_DEFINITIONS


EXPECTED_TOOLS = {
    "doc_search",
    "check_cancellation",
    "check_service_credit",
    "get_sla_target",
    "get_order_details",
    "preview_action",
}

def test_required_tools_exist():
    names = {
        tool["function"]["name"]
        for tool in TOOL_DEFINITIONS
    }

    assert names == EXPECTED_TOOLS


def test_all_tools_are_function_tools():
    for tool in TOOL_DEFINITIONS:
        assert tool["type"] == "function"
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]


def test_tool_parameters_reject_unknown_fields():
    for tool in TOOL_DEFINITIONS:
        schema = tool["function"]["parameters"]

        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False