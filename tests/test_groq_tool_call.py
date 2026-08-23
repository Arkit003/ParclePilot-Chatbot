from src.agent.tool_defs import TOOL_DEFINITIONS
from src.llm.client import get_llm_client, get_model


def test_groq_can_request_tool():
    client = get_llm_client()
    model = get_model()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are testing ParcelPilot tool calling. "
                    "When asked about an SLA, use the "
                    "get_sla_target tool instead of answering "
                    "from memory."
                ),
            },
            {
                "role": "user",
                "content": (
                    "What is the P1 SLA for account ACCT-001?"
                ),
            },
        ],
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
    )

    message = response.choices[0].message

    assert message.tool_calls

    tool_call = message.tool_calls[0]

    assert tool_call.function.name == "get_sla_target"

    print(
        "Tool:",
        tool_call.function.name,
    )

    print(
        "Arguments:",
        tool_call.function.arguments,
    )