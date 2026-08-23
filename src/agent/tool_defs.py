from __future__ import annotations

from typing import Any


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "doc_search",
            "description": (
                "Search ParcelPilot policies, customer agreements, "
                "SOPs, product documentation, and other indexed "
                "documents. Use this for qualitative explanations, "
                "specific policy clauses, known issues, and source "
                "citations. Do not use it for deterministic numeric "
                "business-rule calculations when a structured tool exists."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Natural-language search query describing "
                            "the information you need."
                        ),
                    },
                    "account_id": {
                        "type": ["string", "null"],
                        "description": (
                            "Account ID to scope account-specific "
                            "documents. The server should validate "
                            "this against the authenticated request."
                        ),
                    },
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 20,
                        "default": 5,
                        "description": (
                            "Maximum number of document chunks "
                            "to retrieve."
                        ),
                    },
                    "include_deprecated": {
                        "type": "boolean",
                        "default": False,
                        "description": (
                            "Only set to true when the user explicitly "
                            "asks about historical/deprecated policy."
                        ),
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_cancellation",
            "description": (
                "Deterministically determine whether an order can "
                "be cancelled and calculate the applicable cancellation "
                "fee using the current SOP and customer agreement overrides."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": (
                            "ParcelPilot order ID, for example ORD-1001."
                        ),
                    },
                },
                "required": [
                    "order_id",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_service_credit",
            "description": (
                "Deterministically determine service-credit eligibility "
                "and calculate the credit amount using the current SOP "
                "and customer agreement overrides."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": (
                            "ParcelPilot order ID, for example ORD-2002."
                        ),
                    },
                },
                "required": [
                    "order_id",
                ],
                "additionalProperties": False,
            },
        },
    },
        {
        "type": "function",
        "function": {
            "name": "get_sla_target",
            "description": (
                "Return the applicable ParcelPilot support SLA. "
                "Use account_id for a specific customer account and "
                "plan for plan-level default SLA questions. "
                "Use severity for a specific P1/P2/P3 target. "
                "If severity is omitted, return the complete P1/P2/P3 "
                "SLA matrix. Customer agreement overrides take "
                "precedence over current policy defaults."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": ["string", "null"],
                        "description": (
                            "Customer account ID, for example ACCT-001."
                        ),
                    },
                    "plan": {
                        "type": ["string", "null"],
                        "enum": [
                            "Enterprise",
                            "Growth",
                            "Standard",
                        ],
                        "description": (
                            "ParcelPilot plan for a plan-level SLA query."
                        ),
                    },
                    "severity": {
                        "type": ["string", "null"],
                        "enum": [
                            "P1",
                            "P2",
                            "P3",
                        ],
                        "description": (
                            "Support severity. Omit for all severities."
                        ),
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
    "type": "function",
    "function": {
        "name": "preview_action",
        "description": (
            "Prepare a state-changing support action for "
            "user confirmation. This does not execute the action."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": [
                        "escalation",
                        "ticket_update",
                        "follow_up",
                    ],
                },
                "account_id": {
                    "type": "string",
                },
                "reason": {
                    "type": "string",
                },
                "ticket_id": {
                    "type": ["string", "null"],
                },
                "order_id": {
                    "type": ["string", "null"],
                },
                "amount_inr": {
                    "type": ["integer", "null"],
                    "minimum": 0,
                },
                "details": {
                    "type": "object",
                },
            },
            "required": [
                "action_type",
                "account_id",
                "reason",
            ],
            "additionalProperties": False,
            },
        },
    },
    
]