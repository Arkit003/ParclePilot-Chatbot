import pytest

from src.tools.structured_data import (
    check_cancellation,
    check_service_credit,
    get_sla_target,
)


def test_unknown_order_raises_error():
    with pytest.raises(ValueError, match="Order not found"):
        check_cancellation(
            order_id="ORD-9999",
            request_time="2026-08-16 11:00",
        )


def test_unknown_account_raises_error():
    with pytest.raises(ValueError, match="Account not found"):
        get_sla_target(
            account_id="ACCT-999",
            severity="P1",
        )


def test_invalid_severity_raises_error():
    with pytest.raises(ValueError, match="Unsupported severity"):
        get_sla_target(
            account_id="ACCT-001",
            severity="P4",
        )



def test_northstar_cancellation_override():
    """
    Northstar can cancel any BOOKED shipment before pickup
    without a cancellation fee.
    """

    result = check_cancellation(
        order_id="ORD-1001",
        request_time="2026-08-16 11:00",
    )

    assert result.allowed is True
    assert result.cancellation_fee_inr == 0
    assert result.account_id == "ACCT-001"


def test_lumenworks_cancellation_after_30_minutes():
    """
    LumenWorks has no cancellation-fee waiver, so the
    default ₹250 fee applies after 30 minutes.
    """

    result = check_cancellation(
        order_id="ORD-2001",
        request_time="2026-08-16 10:15",
    )

    assert result.allowed is True
    assert result.cancellation_fee_inr == 250
    assert result.account_id == "ACCT-002"


def test_standard_cancellation_within_30_minutes():
    """
    Beacon Retail uses the default policy.
    ORD-3001 was cancelled 15 minutes after booking.
    """

    result = check_cancellation(
        order_id="ORD-3001",
        request_time="2026-08-16 10:40",
    )

    assert result.allowed is True
    assert result.cancellation_fee_inr == 0
    assert result.account_id == "ACCT-003"


def test_picked_up_cannot_be_cancelled():
    """
    PICKED_UP shipments must not be cancelled.
    """

    result = check_cancellation(
        order_id="ORD-1002",
        request_time="2026-08-16 10:20",
    )

    assert result.allowed is False
    assert result.cancellation_fee_inr == 0


def test_delivered_cannot_be_cancelled():
    """
    DELIVERED shipments cannot be cancelled.
    """

    result = check_cancellation(
        order_id="ORD-4001",
        request_time="2026-08-16 11:00",
    )

    assert result.allowed is False
    assert result.cancellation_fee_inr == 0


# Service-credit tests



def test_lumenworks_service_credit():
    """
    LumenWorks override:
    pickup must be more than 4 hours late,
    carrier fault must exist,
    credit = fixed ₹300.

    ORD-2002:
        pickup window ended = 06:30
        dataset snapshot = 11:00
        delay = 4.5 hours
    """

    result = check_service_credit(
        order_id="ORD-2002",
        request_time="2026-08-16 11:00",
    )

    assert result.eligible is True
    assert result.credit_amount_inr == 300
    assert result.account_id == "ACCT-002"


def test_service_credit_not_eligible_without_carrier_fault():
    """
    Service credit should not be granted when carrier fault
    is not established.
    """

    result = check_service_credit(
        order_id="ORD-1001",
        request_time="2026-08-16 11:00",
    )

    assert result.eligible is False
    assert result.credit_amount_inr == 0



# SLA tests



def test_northstar_sla_override():
    """
    Northstar agreement overrides Enterprise defaults.
    P1 = 15 minutes, 24x7.
    """

    result = get_sla_target(
        account_id="ACCT-001",
        severity="P1",
    )

    assert result.target == "15 minutes, 24x7"
    assert result.account_id == "ACCT-001"


def test_lumenworks_sla_override():
    """
    LumenWorks agreement defines:
    P2 = 4 business hours.
    """

    result = get_sla_target(
        account_id="ACCT-002",
        severity="P2",
    )

    assert result.target == "4 business hours"


def test_beacon_uses_default_sla():
    """
    Beacon has no custom agreement, so the current
    Support Policy v3 applies.

    Standard P2 = 1 business day.
    """

    result = get_sla_target(
        account_id="ACCT-003",
        severity="P2",
    )

    assert result.target == "1 business day"
    assert result.source == "ParcelPilot Support Policy v3"


def test_axis_uses_default_enterprise_sla():
    """
    Axis has no agreement, so Enterprise defaults apply.
    """

    result = get_sla_target(
        account_id="ACCT-004",
        severity="P1",
    )

    assert result.target == "30 minutes, 24x7"

def test_standard_plan_returns_full_sla_matrix():

    result = get_sla_target(
        plan="Standard",
    )

    assert result.plan == "Standard"
    assert result.severity is None

    assert result.targets == {
        "P1": "4 business hours",
        "P2": "1 business day",
        "P3": "2 business days",
    }


def test_standard_plan_p2_returns_single_target():

    result = get_sla_target(
        plan="Standard",
        severity="P2",
    )

    assert result.target == "1 business day"


def test_northstar_returns_full_override_matrix():

    result = get_sla_target(
        account_id="ACCT-001",
    )

    assert result.targets == {
        "P1": "15 minutes, 24x7",
        "P2": "1 hour",
        "P3": "8 business hours",
    }


def test_account_and_plan_cannot_both_be_provided():

    with pytest.raises(
        ValueError,
        match="either account_id or plan",
    ):
        get_sla_target(
            account_id="ACCT-001",
            plan="Enterprise",
        )


def test_sla_requires_account_or_plan():

    with pytest.raises(
        ValueError,
        match="Either account_id or plan",
    ):
        get_sla_target()