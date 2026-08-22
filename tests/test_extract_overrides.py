from pathlib import Path

import pytest

from src.ingestion.extract_overrides import (
    build_override_record,
    extract_account_id,
    extract_customer_name,
    extract_lumenworks_overrides,
    extract_northstar_overrides,
    normalize_text,
)



# Helper / parsing tests



def test_extract_account_id():
    text = "ParcelPilot - Northstar Logistics Enterprise Agreement\nAccount: ACCT-001"

    assert extract_account_id(text) == "ACCT-001"


def test_extract_customer_name_stops_at_next_field():
    text = (
        "Account: ACCT-002 "
        "Customer: LumenWorks "
        "Plan: Growth "
        "Term: 1 March 2026 to 28 February 2027"
    )

    assert extract_customer_name(text) == "LumenWorks"


def test_normalize_text():
    text = "Customer:\u00a0LumenWorks   \n\n   Plan: Growth"

    result = normalize_text(text)

    assert result == "Customer: LumenWorks \n Plan: Growth"


# Northstar override tests



def test_northstar_sla_overrides():
    text = """
    P1: 15 minutes, 24x7
    P2: 1 hour
    P3: 8 business hours
    """

    overrides = extract_northstar_overrides(text)

    assert overrides["sla"] == {
        "P1": "15 minutes, 24x7",
        "P2": "1 hour",
        "P3": "8 business hours",
    }


def test_northstar_cancellation_override():
    text = """
    Northstar may cancel any BOOKED shipment before pickup
    with no cancellation fee, regardless of how long ago
    the shipment was booked.
    """

    overrides = extract_northstar_overrides(text)

    cancellation = overrides["cancellation"]

    assert cancellation["booked_before_pickup"]["fee_inr"] == 0
    assert cancellation["booked_before_pickup"]["fee_waived"] is True


def test_northstar_service_credit_cap():
    text = """
    Monthly aggregate service credits are capped at INR 5,000.
    """

    overrides = extract_northstar_overrides(text)

    assert (
        overrides["service_credit"]["monthly_cap_inr"]
        == 5000
    )



# LumenWorks override tests



def test_lumenworks_sla_overrides():
    text = """
    P1: 2 business hours
    P2: 4 business hours
    P3: 2 business days
    """

    overrides = extract_lumenworks_overrides(text)

    assert overrides["sla"] == {
        "P1": "2 business hours",
        "P2": "4 business hours",
        "P3": "2 business days",
    }


def test_lumenworks_has_no_cancellation_waiver():
    text = """
    No special cancellation-fee waiver applies.
    Use the current ParcelPilot Cancellation & Service Credit SOP.
    """

    overrides = extract_lumenworks_overrides(text)

    cancellation = overrides["cancellation"]

    assert cancellation["booked_before_pickup"]["fee_waived"] is False
    assert cancellation["booked_before_pickup"]["use_default_sop"] is True


def test_lumenworks_service_credit_override():
    text = """
    If a pickup is more than 4 hours past the end of the
    scheduled pickup window, the carrier is at fault, and
    the customer is not at fault, LumenWorks receives a
    fixed INR 300 service credit.
    """

    overrides = extract_lumenworks_overrides(text)

    service_credit = overrides["service_credit"]

    assert service_credit["delay_threshold_hours"] == 4
    assert service_credit["fixed_credit_inr"] == 300
    assert service_credit["requires_carrier_fault"] is True
    assert service_credit["requires_no_customer_fault"] is True
    assert service_credit["replaces_default_sop"] is True



# Full agreement tests



def test_northstar_real_agreement():
    base_dir = Path(__file__).resolve().parents[1]

    pdf_path = (
        base_dir
        / "docs"
        / "05_Northstar_Logistics_Enterprise_Agreement.pdf"
    )

    record = build_override_record(pdf_path)

    assert record["account_id"] == "ACCT-001"
    assert record["customer_name"] == "Northstar Logistics"
    assert record["status"] == "ACTIVE"

    overrides = record["overrides"]

    assert overrides["sla"]["P1"] == "15 minutes, 24x7"

    assert (
        overrides["cancellation"]
        ["booked_before_pickup"]
        ["fee_waived"]
        is True
    )

    assert (
        overrides["service_credit"]["monthly_cap_inr"]
        == 5000
    )


def test_lumenworks_real_agreement():
    base_dir = Path(__file__).resolve().parents[1]

    pdf_path = (
        base_dir
        / "docs"
        / "06_LumenWorks_Service_Agreement.pdf"
    )

    record = build_override_record(pdf_path)

    assert record["account_id"] == "ACCT-002"
    assert record["customer_name"] == "LumenWorks"
    assert record["status"] == "ACTIVE"

    overrides = record["overrides"]

    assert overrides["sla"]["P2"] == "4 business hours"

    service_credit = overrides["service_credit"]

    assert service_credit["delay_threshold_hours"] == 4
    assert service_credit["fixed_credit_inr"] == 300



# Safety / invalid-input tests



def test_missing_pdf_raises_error(tmp_path):
    missing_pdf = tmp_path / "missing.pdf"

    with pytest.raises(FileNotFoundError):
        build_override_record(missing_pdf)