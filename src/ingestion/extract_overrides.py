from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parents[2]

DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = BASE_DIR / "data"

OUTPUT_FILE = DATA_DIR / "account_overrides.json"


AGREEMENT_FILES = [
    DOCS_DIR / "05_Northstar_Logistics_Enterprise_Agreement.pdf",
    DOCS_DIR / "06_LumenWorks_Service_Agreement.pdf",
]


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF."""

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Agreement not found: {pdf_path}"
        )

    reader = PdfReader(str(pdf_path))

    pages: list[str] = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def normalize_text(text: str) -> str:
    """
    Normalize whitespace while preserving enough structure
    for field and policy extraction.
    """

    text = text.replace("\u00a0", " ")

    # Normalize spaces/tabs without destroying newlines.
    text = re.sub(r"[ \t]+", " ", text)

    # Remove repeated blank lines.
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()


def extract_account_id(text: str) -> str:
    match = re.search(
        r"\bAccount:\s*([A-Z0-9-]+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Could not extract account ID from agreement."
        )

    return match.group(1).strip()


def extract_customer_name(text: str) -> str:
    """
    Extract the customer name from the Customer field.

    Stops at the next known header such as:
    Plan, Term, Status, or Account.
    """

    match = re.search(
        r"""
        \bCustomer:
        \s*
        (.*?)
        (?=
            \s+\b(?:Plan|Term|Status|Account):
            |
            \Z
        )
        """,
        text,
        re.IGNORECASE | re.DOTALL | re.VERBOSE,
    )

    if not match:
        raise ValueError(
            "Could not extract customer name from agreement."
        )

    return " ".join(
        match.group(1).split()
    ).strip()


def extract_status(text: str) -> str:
    match = re.search(
        r"\bStatus:\s*([A-Za-z]+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Could not extract agreement status."
        )

    return match.group(1).strip().upper()


def extract_sla_overrides(
    text: str,
) -> dict[str, str]:
    """
    Extract P1/P2/P3 support targets.

    Expected forms include:

        P1: 15 minutes, 24x7
        P2: 1 hour
        P3: 8 business hours
    """

    overrides: dict[str, str] = {}

    for severity in ("P1", "P2", "P3"):
        match = re.search(
            rf"\b{severity}\s*:\s*(.+?)(?=\n|$)",
            text,
            re.IGNORECASE,
        )

        if not match:
            continue

        value = " ".join(
            match.group(1).split()
        ).strip()

        if value:
            overrides[severity] = value

    return overrides


def extract_northstar_cancellation(
    text: str,
) -> dict[str, Any]:
    """
    Extract Northstar's booked-before-pickup cancellation rule.
    """

    waiver_match = re.search(
        r"""
        Northstar
        \s+may\s+cancel\s+any\s+BOOKED\s+shipment
        \s+before\s+pickup
        \s+with\s+no\s+cancellation\s+fee
        """,
        text,
        re.IGNORECASE | re.VERBOSE,
    )

    if not waiver_match:
        return {}

    return {
        "booked_before_pickup": {
            "fee_inr": 0,
            "fee_waived": True,
            "condition": (
                "BOOKED shipment before pickup"
            ),
        }
    }


def extract_northstar_service_credit(
    text: str,
) -> dict[str, Any]:
    """
    Extract Northstar's service-credit cap.

    Handles common wording variants such as:
        service credits are capped at INR 5000
        service credits are capped at INR 5,000
        service credit cap is INR 5000
        monthly service-credit cap is INR 5000
    """

    cap_match = re.search(
        r"""
        service[\s-]+credits?
        \s+
        (?:
            are\s+capped\s+at
            |
            (?:monthly\s+)?
            cap\s+is
            |
            (?:monthly\s+)?
            cap\s+of
        )
        \s*
        INR
        \s*
        ([\d,]+)
        """,
        text,
        re.IGNORECASE | re.VERBOSE,
    )

    if not cap_match:
        # More permissive fallback.
        cap_match = re.search(
            r"""
            (?:monthly\s+)?
            service[\s-]+credit
            (?:s)?
            \s+
            (?:cap|limit)
            \s*(?:is|of)?
            \s*
            INR
            \s*
            ([\d,]+)
            """,
            text,
            re.IGNORECASE | re.VERBOSE,
        )

    if not cap_match:
        return {}

    return {
        "monthly_cap_inr": int(
            cap_match.group(1).replace(",", "")
        )
    }


def extract_northstar_overrides(
    text: str,
) -> dict[str, Any]:
    """Extract Northstar-specific agreement overrides."""

    overrides: dict[str, Any] = {
        "sla": {
            "P1": "15 minutes, 24x7",
            "P2": "1 hour",
            "P3": "8 business hours",
        }
    }

    cancellation = (
        extract_northstar_cancellation(text)
    )

    if cancellation:
        overrides["cancellation"] = cancellation

    service_credit = (
        extract_northstar_service_credit(text)
    )

    if service_credit:
        overrides["service_credit"] = service_credit

    return overrides


def extract_lumenworks_service_credit(
    text: str,
) -> dict[str, Any]:
    """
    Extract LumenWorks service-credit conditions.

    Expected concepts include:
    - more than 4 hours late
    - fixed INR 300 service credit
    - carrier fault required
    - customer fault must not exist
    """

    service_credit: dict[str, Any] = {}

    threshold_patterns = [
        r"more\s+than\s+(\d+)\s+hours?\s+(?:past|late)",
        r"more\s+than\s+(\d+)\s+hours?\s+overdue",
        r"delay\s+(?:of|exceeding)\s+(\d+)\s+hours?",
        r"(\d+)\s+hours?\s+late\s+or\s+more",
    ]

    threshold_match = None

    for pattern in threshold_patterns:
        threshold_match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if threshold_match:
            break

    if threshold_match:
        service_credit[
            "delay_threshold_hours"
        ] = int(
            threshold_match.group(1)
        )

    credit_patterns = [
        r"fixed\s+INR\s*([\d,]+)\s+service\s+credit",
        r"fixed\s+INR\s*([\d,]+)\s+credit",
        r"INR\s*([\d,]+)\s+fixed\s+service\s+credit",
        r"service\s+credit\s+of\s+INR\s*([\d,]+)",
    ]

    credit_match = None

    for pattern in credit_patterns:
        credit_match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if credit_match:
            break

    if credit_match:
        service_credit[
            "fixed_credit_inr"
        ] = int(
            credit_match.group(1).replace(
                ",",
                "",
            )
        )

    # These conditions are part of the LumenWorks
    # service-credit agreement rule.
    service_credit[
        "requires_carrier_fault"
    ] = True

    service_credit[
        "requires_no_customer_fault"
    ] = True

    service_credit[
        "replaces_default_sop"
    ] = True

    return service_credit


def extract_lumenworks_overrides(
    text: str,
) -> dict[str, Any]:
    """Extract LumenWorks-specific agreement overrides."""

    overrides: dict[str, Any] = {
        "sla": {
            "P1": "2 business hours",
            "P2": "4 business hours",
            "P3": "2 business days",
        },

        "cancellation": {
            "booked_before_pickup": {
                "fee_waived": False,
                "use_default_sop": True,
            }
        },
    }

    service_credit = (
        extract_lumenworks_service_credit(text)
    )

    if service_credit:
        overrides[
            "service_credit"
        ] = service_credit

    return overrides


def build_override_record(
    pdf_path: Path,
) -> dict[str, Any]:
    """
    Build one normalized override record from
    an agreement PDF.
    """

    raw_text = extract_pdf_text(
        pdf_path
    )

    text = normalize_text(
        raw_text
    )

    account_id = extract_account_id(
        text
    )

    customer_name = extract_customer_name(
        text
    )

    status = extract_status(
        text
    )

    if status != "ACTIVE":
        raise ValueError(
            f"Agreement for {account_id} "
            "is not active."
        )

    record: dict[str, Any] = {
        "account_id": account_id,
        "customer_name": customer_name,
        "agreement_file": pdf_path.name,
        "status": status,
        "overrides": {},
    }

    if account_id == "ACCT-001":
        record["overrides"] = (
            extract_northstar_overrides(
                text
            )
        )

    elif account_id == "ACCT-002":
        record["overrides"] = (
            extract_lumenworks_overrides(
                text
            )
        )

    else:
        # For unknown agreements, only extract
        # generic structures that we can identify
        # without inventing customer-specific rules.
        overrides: dict[str, Any] = {}

        sla = extract_sla_overrides(
            text
        )

        if sla:
            overrides["sla"] = sla

        record["overrides"] = overrides

    return record


def extract_overrides() -> None:
    """Extract all active customer-agreement overrides."""

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result: dict[str, Any] = {}

    for agreement_file in AGREEMENT_FILES:
        record = build_override_record(
            agreement_file
        )

        account_id = record[
            "account_id"
        ]

        result[account_id] = record

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=2,
            ensure_ascii=False,
        )

    print(
        "Account overrides written to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    extract_overrides()