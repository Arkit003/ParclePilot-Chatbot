from __future__ import annotations

from dataclasses import dataclass

from src.agent.loop import AgentLoop


# ---------------------------------------------------------
# Mock OpenAI-style response objects
# ---------------------------------------------------------


@dataclass
class MockFunction:
    name: str
    arguments: str


@dataclass
class MockToolCall:
    id: str
    function: MockFunction


@dataclass
class MockMessage:
    content: str | None = None
    tool_calls: list[MockToolCall] | None = None


@dataclass
class MockChoice:
    message: MockMessage


@dataclass
class MockResponse:
    choices: list[MockChoice]


# ---------------------------------------------------------
# Mock Chat Completions
# ---------------------------------------------------------


class MockCompletions:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)

        if not self.responses:
            raise RuntimeError(
                "Mock LLM has no more responses."
            )

        return self.responses.pop(0)


class MockChat:
    def __init__(self, responses):
        self.completions = MockCompletions(
            responses
        )


class MockLLMClient:
    def __init__(self, responses):
        self.chat = MockChat(responses)


# ---------------------------------------------------------
# Fake tool
# ---------------------------------------------------------


def fake_check_cancellation(
    order_id: str,
    request_time: str,
):
    return {
        "order_id": order_id,
        "allowed": True,
        "cancellation_fee_inr": 0,
        "request_time": request_time,
    }

def test_agent_tool_call_then_final_answer(
    monkeypatch,
):
    from src.agent import tool_registry

    monkeypatch.setitem(
        tool_registry.TOOL_REGISTRY,
        "check_cancellation",
        fake_check_cancellation,
    )

    responses = [
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        content=None,
                        tool_calls=[
                            MockToolCall(
                                id="call_1",
                                function=MockFunction(
                                    name="check_cancellation",
                                    arguments=(
                                        '{"order_id": "ORD-1001", '
                                        '"request_time": '
                                        '"2026-08-16 11:00"}'
                                    ),
                                ),
                            )
                        ],
                    )
                )
            ]
        ),
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        content=(
                            "ORD-1001 can be cancelled "
                            "without a fee."
                        ),
                        tool_calls=None,
                    )
                )
            ]
        ),
    ]

    client = MockLLMClient(responses)

    agent = AgentLoop(
        llm_client=client,
        model="mock-model",
    )

    result = agent.run(
        messages=[
            {
                "role": "user",
                "content": (
                    "Can ORD-1001 be cancelled "
                    "without a fee?"
                ),
            }
        ]
    )

    assert result == (
        "ORD-1001 can be cancelled "
        "without a fee."
    )

    assert len(
        client.chat.completions.calls
    ) == 2

def test_unknown_tool_returns_error_to_llm():

    responses = [
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        tool_calls=[
                            MockToolCall(
                                id="call_1",
                                function=MockFunction(
                                    name="does_not_exist",
                                    arguments="{}",
                                ),
                            )
                        ],
                    )
                )
            ]
        ),
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        content="I could not execute that tool.",
                    )
                )
            ]
        ),
    ]

    client = MockLLMClient(responses)

    agent = AgentLoop(
        llm_client=client,
        model="mock-model",
    )

    result = agent.run(
        messages=[
            {
                "role": "user",
                "content": "Do something.",
            }
        ]
    )

    assert result == (
        "I could not execute that tool."
    )

    assert len(
        client.chat.completions.calls
    ) == 2

def test_invalid_tool_arguments():

    responses = [
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        tool_calls=[
                            MockToolCall(
                                id="call_1",
                                function=MockFunction(
                                    name="check_cancellation",
                                    arguments="{broken json}",
                                ),
                            )
                        ],
                    )
                )
            ]
        ),
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        content="The tool request was invalid.",
                    )
                )
            ]
        ),
    ]

    client = MockLLMClient(responses)

    agent = AgentLoop(
        llm_client=client,
        model="mock-model",
    )

    result = agent.run(
        messages=[
            {
                "role": "user",
                "content": "Check cancellation.",
            }
        ]
    )

    assert result == (
        "The tool request was invalid."
    )

def failing_tool(**kwargs):
    raise ValueError(
        "Database unavailable."
    )


def test_tool_exception_is_returned_to_llm(
    monkeypatch,
):
    from src.agent import tool_registry

    monkeypatch.setitem(
        tool_registry.TOOL_REGISTRY,
        "check_cancellation",
        failing_tool,
    )

    responses = [
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        tool_calls=[
                            MockToolCall(
                                id="call_1",
                                function=MockFunction(
                                    name="check_cancellation",
                                    arguments=(
                                        '{"order_id": "ORD-1001", '
                                        '"request_time": '
                                        '"2026-08-16 11:00"}'
                                    ),
                                ),
                            )
                        ],
                    )
                )
            ]
        ),
        MockResponse(
            choices=[
                MockChoice(
                    message=MockMessage(
                        content=(
                            "I could not complete the "
                            "cancellation check."
                        )
                    )
                )
            ]
        ),
    ]

    client = MockLLMClient(responses)

    agent = AgentLoop(
        llm_client=client,
        model="mock-model",
    )

    result = agent.run(
        messages=[
            {
                "role": "user",
                "content": "Check cancellation.",
            }
        ]
    )

    assert result == (
        "I could not complete the "
        "cancellation check."
    )

def test_agent_stops_after_five_iterations(
    monkeypatch,
):
    from src.agent import tool_registry

    monkeypatch.setitem(
        tool_registry.TOOL_REGISTRY,
        "check_cancellation",
        fake_check_cancellation,
    )

    responses = []

    for index in range(5):
        responses.append(
            MockResponse(
                choices=[
                    MockChoice(
                        message=MockMessage(
                            tool_calls=[
                                MockToolCall(
                                    id=f"call_{index}",
                                    function=MockFunction(
                                        name="check_cancellation",
                                        arguments=(
                                            '{"order_id": '
                                            '"ORD-1001", '
                                            '"request_time": '
                                            '"2026-08-16 11:00"}'
                                        ),
                                    ),
                                )
                            ],
                        )
                    )
                ]
            )
        )

    client = MockLLMClient(responses)

    agent = AgentLoop(
        llm_client=client,
        model="mock-model",
    )

    result = agent.run(
        messages=[
            {
                "role": "user",
                "content": "Check this.",
            }
        ]
    )

    assert result == (
        "I couldn't complete the request within the "
        "allowed reasoning steps. Please try simplifying "
        "the request or request human support."
    )

    assert len(
        client.chat.completions.calls
    ) == 5