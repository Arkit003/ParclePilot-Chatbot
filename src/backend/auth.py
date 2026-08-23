from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    role: str
    account_id: str | None


MOCK_USERS = {
    # Customer users
    "customer-northstar": AuthenticatedUser(
        user_id="customer-northstar",
        role="customer",
        account_id="ACCT-001",
    ),
    "customer-lumenworks": AuthenticatedUser(
        user_id="customer-lumenworks",
        role="customer",
        account_id="ACCT-002",
    ),
    "customer-beacon": AuthenticatedUser(
        user_id="customer-beacon",
        role="customer",
        account_id="ACCT-003",
    ),
    "customer-axis": AuthenticatedUser(
        user_id="customer-axis",
        role="customer",
        account_id="ACCT-004",
    ),

    # Internal support staff
    "rohit": AuthenticatedUser(
        user_id="rohit",
        role="support_agent",
        account_id=None,
    ),
    "maya": AuthenticatedUser(
        user_id="maya",
        role="support_agent",
        account_id=None,
    ),

    # Manager
    "manager": AuthenticatedUser(
        user_id="manager",
        role="manager",
        account_id=None,
    ),
}

def authenticate_request(request: Request) -> AuthenticatedUser:
    """
    Resolve the current user from a mocked request header.

    Header:
        X-User-ID
    """

    user_id = request.headers.get(
        "X-User-ID",
        "support-agent",
    )

    user = MOCK_USERS.get(user_id)

    if user is None:
        raise ValueError(
            f"Unknown mock user: {user_id}"
        )

    return user


def build_request_context(
    request: Request,
) -> tuple[AuthenticatedUser, str]:
    """
    Build request identity + request ID.

    The dataset snapshot is intentionally handled
    separately so it remains a trusted application value.
    """

    user = authenticate_request(request)

    request_id = request.headers.get(
        "X-Request-ID"
    )

    if not request_id:
        request_id = str(uuid.uuid4())

    return user, request_id