from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


ActionType = Literal[
    "escalation",
    "ticket_update",
    "follow_up",
]


class PreviewActionInput(BaseModel):
    action_type: ActionType

    account_id: str

    reason: str = Field(
        min_length=1,
    )

    ticket_id: str | None = None

    order_id: str | None = None

    amount_inr: int | None = Field(
        default=None,
        ge=0,
    )

    details: dict[str, Any] = Field(
        default_factory=dict,
    )


class PreviewActionResult(BaseModel):
    confirmation_id: str
    action_type: ActionType
    account_id: str

    summary: str

    amount_inr: int | None

    requires_manager_approval: bool

    status: Literal["PENDING"] = "PENDING"


class ExecuteActionInput(BaseModel):
    confirmation_id: str

    confirmed: bool = True


class ExecuteActionResult(BaseModel):
    confirmation_id: str

    action_type: ActionType
    account_id: str

    status: Literal[
        "EXECUTED",
        "CANCELLED",
        "REJECTED",
    ]

    message: str