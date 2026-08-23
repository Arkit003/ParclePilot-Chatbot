from fastapi import Request

from src.backend.auth import (
    MOCK_USERS,
    authenticate_request,
)


def test_northstar_customer_exists():
    user = MOCK_USERS["customer-northstar"]

    assert user.role == "customer"
    assert user.account_id == "ACCT-001"


def test_lumenworks_customer_exists():
    user = MOCK_USERS["customer-lumenworks"]

    assert user.role == "customer"
    assert user.account_id == "ACCT-002"


def test_support_agent_has_no_account_scope():
    user = MOCK_USERS["support-agent"]

    assert user.role == "support_agent"
    assert user.account_id is None