from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.agent.guardrails import RequestContext
from src.tools.actions import execute_action
from src.schemas.actions_schema import (
    ExecuteActionInput,
    ExecuteActionResult,
)


router = APIRouter(
    prefix="/actions",
    tags=["actions"],
)


@router.post(
    "/{confirmation_id}/execute",
    response_model=ExecuteActionResult,
)
def execute_pending_action(
    confirmation_id: str,
    confirmed: bool,
):
    """
    Execute a previously previewed action after
    explicit user confirmation.
    """

    # Temporary mocked identity.
    #
    # Later this will come from auth middleware.
    context = RequestContext(
        user_id="mock-user",
        role="support_agent",
        account_id=None,
        request_id="mock-request",
        dataset_snapshot="2026-08-16 11:00",
    )

    try:
        result = execute_action(
            request=ExecuteActionInput(
                confirmation_id=confirmation_id,
                confirmed=confirmed,
            ),
            acting_role=context.role,
            acting_user_id=context.user_id,
        )

        return result

    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc