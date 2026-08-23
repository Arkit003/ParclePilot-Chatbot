from __future__ import annotations

from src.agent.guardrails import RequestContext
from src.agent.loop import AgentLoop
from src.llm.client import get_llm_client, get_model


def test_groq_agent_end_to_end():

    client = get_llm_client()
    model = get_model()

    agent = AgentLoop(
        llm_client=client,
        model=model,
    )

    context = RequestContext(
        user_id="integration-test-user",
        role="support_agent",
        account_id=None,
        request_id="groq-e2e-001",
    )

    result = agent.run(
        messages=[
            {
                "role": "user",
                "content": (
                    "Can Northstar cancel ORD-1001 "
                    "without a cancellation fee? "
                    "Explain why and cite the relevant source."
                ),
            }
        ],
        context=context,
    )

    print("\n========== AGENT RESPONSE ==========\n")
    print(result)
    print("\n====================================\n")

    assert result
    assert len(result.strip()) > 0