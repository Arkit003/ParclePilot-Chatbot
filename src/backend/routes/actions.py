from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from src.backend.auth import build_request_context
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
    request: Request,
    confirmed: bool,
) -> ExecuteActionResult:

    # Resolve identity from the trusted request context.
    try:
        user, _ = build_request_context(request)

    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    try:
        result = execute_action(
            request=ExecuteActionInput(
                confirmation_id=confirmation_id,
                confirmed=confirmed,
            ),
            acting_role=user.role,
            acting_user_id=user.user_id,
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