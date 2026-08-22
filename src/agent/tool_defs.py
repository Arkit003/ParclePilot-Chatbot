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
                    "request_time": {
                        "type": "string",
                        "description": (
                            "Time at which the cancellation request "
                            "is being evaluated, in the dataset's "
                            "reference time format."
                        ),
                    },
                },
                "required": [
                    "order_id",
                    "request_time",
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
                    "request_time": {
                        "type": "string",
                        "description": (
                            "Time at which the service-credit request "
                            "is being evaluated, using the dataset's "
                            "reference time."
                        ),
                    },
                },
                "required": [
                    "order_id",
                    "request_time",
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
                "Return the applicable first-response SLA target for "
                "an account and severity. Customer agreement overrides "
                "take precedence over current policy defaults."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "account_id": {
                        "type": "string",
                        "description": (
                            "ParcelPilot account ID."
                        ),
                    },
                    "severity": {
                        "type": "string",
                        "enum": [
                            "P1",
                            "P2",
                            "P3",
                        ],
                        "description": (
                            "Support severity."
                        ),
                    },
                },
                "required": [
                    "account_id",
                    "severity",
                ],
                "additionalProperties": False,
            },
        },
    },
]