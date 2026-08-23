from __future__ import annotations

import pytest

from src.agent.guardrails import (
    GuardrailEngine,
    GuardrailViolation,
    RequestContext,
)


@pytest.fixture
def guardrails():
    return GuardrailEngine()


@pytest.fixture
def customer_context():
    return RequestContext(
        user_id="user-001",
        role="customer",
        account_id="ACCT-001",
        request_id="req-001",
        dataset_snapshot="2026-08-16 11:00",
    )


@pytest.fixture
def support_context():
    return RequestContext(
        user_id="user-002",
        role="support_agent",
        account_id=None,
        request_id="req-002",
        dataset_snapshot="2026-08-16 11:00",
    )


@pytest.fixture
def manager_context():
    return RequestContext(
        user_id="user-003",
        role="manager",
        account_id=None,
        request_id="req-003",
        dataset_snapshot="2026-08-16 11:00",
    )



# INPUT GUARDRAIL



def test_input_guardrail_accepts_valid_customer_request(
    guardrails,
    customer_context,
):
    result = guardrails.check_input(
        user_message="Can I cancel my shipment?",
        context=customer_context,
    )

    assert result.allowed is True


def test_input_guardrail_rejects_empty_message(
    guardrails,
    customer_context,
):
    result = guardrails.check_input(
        user_message="   ",
        context=customer_context,
    )

    assert result.allowed is False
    assert "empty" in result.reason.lower()


def test_input_guardrail_rejects_unknown_role(
    guardrails,
):
    context = RequestContext(
        user_id="user-001",
        role="admin",
        account_id=None,
        request_id="req-001",
        dataset_snapshot="2026-08-16 11:00",
    )

    result = guardrails.check_input(
        user_message="Hello",
        context=context,
    )

    assert result.allowed is False
    assert "unsupported role" in result.reason.lower()


def test_customer_requires_account(
    guardrails,
):
    context = RequestContext(
        user_id="user-001",
        role="customer",
        account_id=None,
        request_id="req-001",
        dataset_snapshot="2026-08-16 11:00",
    )

    result = guardrails.check_input(
        user_message="Hello",
        context=context,
    )

    assert result.allowed is False
    assert "account context" in result.reason.lower()



# PRE-TOOL GUARDRAIL



def test_customer_can_access_own_sla(
    guardrails,
    customer_context,
):
    result = guardrails.check_pre_tool(
        tool_name="get_sla_target",
        arguments={
            "account_id": "ACCT-001",
            "severity": "P1",
        },
        context=customer_context,
    )

    assert result.allowed is True


def test_customer_cannot_access_other_account_sla(
    guardrails,
    customer_context,
):
    result = guardrails.check_pre_tool(
        tool_name="get_sla_target",
        arguments={
            "account_id": "ACCT-002",
            "severity": "P1",
        },
        context=customer_context,
    )

    assert result.allowed is False
    assert (
        "authenticated account"
        in result.reason.lower()
    )


def test_customer_doc_search_is_scoped_to_own_account(
    guardrails,
    customer_context,
):
    arguments = {
        "query": "cancellation policy"
    }

    result = guardrails.check_pre_tool(
        tool_name="doc_search",
        arguments=arguments,
        context=customer_context,
    )

    assert result.allowed is True
    assert arguments["account_id"] == "ACCT-001"


def test_customer_cannot_search_other_account_documents(
    guardrails,
    customer_context,
):
    result = guardrails.check_pre_tool(
        tool_name="doc_search",
        arguments={
            "query": "service agreement",
            "account_id": "ACCT-002",
        },
        context=customer_context,
    )

    assert result.allowed is False


def test_support_agent_can_access_other_accounts(
    guardrails,
    support_context,
):
    result = guardrails.check_pre_tool(
        tool_name="get_sla_target",
        arguments={
            "account_id": "ACCT-002",
            "severity": "P1",
        },
        context=support_context,
    )

    assert result.allowed is True


def test_manager_can_access_other_accounts(
    guardrails,
    manager_context,
):
    result = guardrails.check_pre_tool(
        tool_name="get_sla_target",
        arguments={
            "account_id": "ACCT-002",
            "severity": "P1",
        },
        context=manager_context,
    )

    assert result.allowed is True


def test_unknown_tool_is_blocked(
    guardrails,
    support_context,
):
    result = guardrails.check_pre_tool(
        tool_name="delete_everything",
        arguments={},
        context=support_context,
    )

    assert result.allowed is False


def test_deprecated_search_can_be_explicitly_requested(
    guardrails,
    support_context,
):
    result = guardrails.check_pre_tool(
        tool_name="doc_search",
        arguments={
            "query": "old support policy",
            "include_deprecated": True,
        },
        context=support_context,
    )

    assert result.allowed is True
    assert result.metadata["historical_search"] is True


# ORDER-BASED ACCOUNT SCOPING



def test_customer_can_access_own_order(
    guardrails,
    customer_context,
):
    result = guardrails.check_pre_tool(
        tool_name="check_cancellation",
        arguments={
            "order_id": "ORD-1001",
            "request_time": "2026-08-16 11:00",
        },
        context=customer_context,
    )

    assert result.allowed is True


def test_customer_cannot_access_other_account_order(
    guardrails,
    customer_context,
):
    # ORD-2001 belongs to ACCT-002.
    result = guardrails.check_pre_tool(
        tool_name="check_cancellation",
        arguments={
            "order_id": "ORD-2001",
            "request_time": "2026-08-16 11:00",
        },
        context=customer_context,
    )

    assert result.allowed is False



# POST-TOOL GUARDRAIL



def test_post_tool_allows_valid_result(
    guardrails,
    support_context,
):
    result = guardrails.check_post_tool(
        tool_name="check_cancellation",
        arguments={
            "order_id": "ORD-1001",
            "request_time": "2026-08-16 11:00",
        },
        result={
            "allowed": True,
            "cancellation_fee_inr": 0,
            "source": "Northstar Agreement",
        },
        context=support_context,
    )

    assert result.allowed is True
    assert result.metadata["source"] == "Northstar Agreement"


def test_post_tool_blocks_deprecated_result(
    guardrails,
    support_context,
):
    result = guardrails.check_post_tool(
        tool_name="doc_search",
        arguments={
            "query": "old policy",
        },
        result={
            "status": "DEPRECATED",
            "source": "Support Policy v2",
        },
        context=support_context,
    )

    assert result.allowed is False
    assert "deprecated" in result.reason.lower()


def test_post_tool_blocks_deprecated_source_name(
    guardrails,
    support_context,
):
    result = guardrails.check_post_tool(
        tool_name="doc_search",
        arguments={
            "query": "old policy",
        },
        result={
            "source": "02_Support_Policy_v2_DEPRECATED.pdf",
        },
        context=support_context,
    )

    assert result.allowed is False



# OUTPUT GUARDRAIL



def test_output_guardrail_allows_plain_answer_without_tools(
    guardrails,
    customer_context,
):
    result = guardrails.check_output(
        answer="Hello, how can I help?",
        context=customer_context,
        tool_results=[],
    )

    assert result.allowed is True


def test_output_guardrail_rejects_empty_answer(
    guardrails,
    customer_context,
):
    result = guardrails.check_output(
        answer="   ",
        context=customer_context,
        tool_results=[],
    )

    assert result.allowed is False


def test_output_guardrail_requires_source_for_tool_answer(
    guardrails,
    support_context,
):
    result = guardrails.check_output(
        answer="The cancellation fee is ₹0.",
        context=support_context,
        tool_results=[
            {
                "tool": "check_cancellation",
                "source": None,
            }
        ],
    )

    assert result.allowed is False


def test_output_guardrail_accepts_traceable_tool_answer(
    guardrails,
    support_context,
):
    result = guardrails.check_output(
        answer="The cancellation fee is ₹0.",
        context=support_context,
        tool_results=[
            {
                "tool": "check_cancellation",
                "source": "Northstar Agreement",
            }
        ],
    )

    assert result.allowed is True