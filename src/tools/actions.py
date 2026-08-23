from __future__ import annotations

import json
import logging
import secrets
import sqlite3
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

from src.schemas.actions_schema import (
    ExecuteActionInput,
    ExecuteActionResult,
    PreviewActionInput,
    PreviewActionResult,
)


logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parents[2]

ACTIONS_DB = BASE_DIR / "data" / "actions.db"

MANAGER_APPROVAL_THRESHOLD = 1_000


def _connect() -> sqlite3.Connection:
    ACTIONS_DB.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        ACTIONS_DB
    )

    connection.row_factory = sqlite3.Row

    return connection


def _initialize_database() -> None:
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS actions (
                confirmation_id TEXT PRIMARY KEY,

                action_type TEXT NOT NULL,

                account_id TEXT NOT NULL,

                reason TEXT NOT NULL,

                ticket_id TEXT,

                order_id TEXT,

                amount_inr INTEGER,

                details TEXT NOT NULL,

                status TEXT NOT NULL,

                created_at TEXT NOT NULL,

                executed_at TEXT,

                approved_by TEXT
            )
            """
        )

        connection.commit()


_initialize_database()


def preview_action(
    request: PreviewActionInput,
) -> PreviewActionResult:
    """
    Prepare a state-changing action.

    IMPORTANT:
    This function does not mutate any ParcelPilot
    operational state. It only creates a pending action.
    """

    confirmation_id = secrets.token_urlsafe(
        18
    )

    requires_manager_approval = (
        request.amount_inr is not None
        and request.amount_inr
        > MANAGER_APPROVAL_THRESHOLD
    )

    summary = _build_summary(
        request
    )

    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO actions (
                confirmation_id,
                action_type,
                account_id,
                reason,
                ticket_id,
                order_id,
                amount_inr,
                details,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                confirmation_id,
                request.action_type,
                request.account_id,
                request.reason,
                request.ticket_id,
                request.order_id,
                request.amount_inr,
                json.dumps(
                    request.details
                ),
                "PENDING",
                datetime.now(timezone.utc).isoformat()
            ),
        )

        connection.commit()

    logger.info(
        "Action preview created | "
        "confirmation_id=%s | action_type=%s | "
        "account_id=%s | amount=%s",
        confirmation_id,
        request.action_type,
        request.account_id,
        request.amount_inr,
    )

    return PreviewActionResult(
        confirmation_id=confirmation_id,
        action_type=request.action_type,
        account_id=request.account_id,
        summary=summary,
        amount_inr=request.amount_inr,
        requires_manager_approval=(
            requires_manager_approval
        ),
    )


def execute_action(
    request: ExecuteActionInput,
    acting_role: str,
    acting_user_id: str,
    acting_account_id: str | None = None,
) -> ExecuteActionResult:
    """
    Execute a previously previewed action.

    Execution requires:
    1. Existing confirmation ID.
    2. Action is still PENDING.
    3. Explicit confirmation.
    4. Valid role.
    5. Correct account scope when applicable.
    6. Manager approval when required.
    """

    # --------------------------------------------------
    # Explicit rejection
    # --------------------------------------------------

    if not request.confirmed:
        return _cancel_action(
            request.confirmation_id
        )

    with _connect() as connection:

        # --------------------------------------------------
        # Find action
        # --------------------------------------------------

        action = connection.execute(
            """
            SELECT *
            FROM actions
            WHERE confirmation_id = ?
            """,
            (
                request.confirmation_id,
            ),
        ).fetchone()

        # --------------------------------------------------
        # Confirmation must exist
        # --------------------------------------------------

        if action is None:
            raise ValueError(
                "Confirmation ID not found."
            )

        # --------------------------------------------------
        # Action must still be pending
        # --------------------------------------------------

        if action["status"] != "PENDING":
            raise ValueError(
                f"Action is already "
                f"{action['status']}."
            )

        # --------------------------------------------------
        # Role authorization
        # --------------------------------------------------

        if acting_role not in {
            "support_agent",
            "manager",
        }:
            raise PermissionError(
                "This role cannot execute "
                "state-changing actions."
            )

        # --------------------------------------------------
        # Account authorization
        # --------------------------------------------------

        action_account_id = action["account_id"]

        if (
            acting_account_id is not None
            and acting_account_id != action_account_id
        ):
            raise PermissionError(
                "You are not authorized to execute "
                "an action for this account."
            )

        # --------------------------------------------------
        # Manager approval
        # --------------------------------------------------

        amount = action["amount_inr"] or 0

        if amount > MANAGER_APPROVAL_THRESHOLD:

            if acting_role != "manager":
                raise PermissionError(
                    "Manager approval is required "
                    "for actions above ₹1,000."
                )

        # --------------------------------------------------
        # Execute
        # --------------------------------------------------

        now = datetime.now(
            timezone.utc
        ).isoformat()

        connection.execute(
            """
            UPDATE actions
            SET
                status = 'EXECUTED',
                executed_at = ?,
                approved_by = ?
            WHERE confirmation_id = ?
            """,
            (
                now,
                acting_user_id,
                request.confirmation_id,
            ),
        )

        connection.commit()

    logger.info(
        "Action executed | "
        "confirmation_id=%s | "
        "action_type=%s | "
        "account_id=%s | "
        "acting_role=%s",
        request.confirmation_id,
        action["action_type"],
        action["account_id"],
        acting_role,
    )

    return ExecuteActionResult(
        confirmation_id=request.confirmation_id,
        action_type=action["action_type"],
        account_id=action["account_id"],
        status="EXECUTED",
        message="Action executed successfully.",
    )


def _cancel_action(
    confirmation_id: str,
) -> ExecuteActionResult:

    with _connect() as connection:

        action = connection.execute(
            """
            SELECT *
            FROM actions
            WHERE confirmation_id = ?
            """,
            (
                confirmation_id,
            ),
        ).fetchone()

        if action is None:
            raise ValueError(
                "Confirmation ID not found."
            )

        if action["status"] != "PENDING":
            raise ValueError(
                f"Action is already "
                f"{action['status']}."
            )

        connection.execute(
            """
            UPDATE actions
            SET status = 'CANCELLED'
            WHERE confirmation_id = ?
            """,
            (
                confirmation_id,
            ),
        )

        connection.commit()

    return ExecuteActionResult(
        confirmation_id=confirmation_id,
        action_type=action["action_type"],
        account_id=action["account_id"],
        status="CANCELLED",
        message="Action cancelled.",
    )


def _build_summary(
    request: PreviewActionInput,
) -> str:

    if request.action_type == "escalation":
        return (
            f"Escalate the issue for account "
            f"{request.account_id}: "
            f"{request.reason}"
        )

    if request.action_type == "ticket_update":
        return (
            f"Update ticket "
            f"{request.ticket_id}: "
            f"{request.reason}"
        )

    if request.action_type == "follow_up":
        return (
            f"Create a follow-up for "
            f"{request.account_id}: "
            f"{request.reason}"
        )

    raise ValueError(
        f"Unsupported action type: "
        f"{request.action_type}"
    )