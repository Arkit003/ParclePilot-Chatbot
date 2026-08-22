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

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


def normalize_text(text: str) -> str:
    """Normalize whitespace while preserving useful text."""

    text = text.replace("\u00a0", " ")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)

    return text.strip()


def extract_account_id(text: str) -> str:
    match = re.search(
        r"Account:\s*([A-Z0-9-]+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Could not extract account ID from agreement."
        )

    return match.group(1).strip()


def extract_customer_name(text: str) -> str:
    match = re.search(
        r"Customer:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        raise ValueError(
            "Could not extract customer name from agreement."
        )

    return match.group(1).strip()


def extract_status(text: str) -> str:
    match = re.search(
        r"Status:\s*(\w+)",
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

    Expected form:

        P1: ...
        P2: ...
        P3: ...
    """

    overrides: dict[str, str] = {}

    for severity in ("P1", "P2", "P3"):
        pattern = rf"{severity}:\s*(.+)"

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()

            # Remove trailing sentence fragments where possible.
            value = value.split("\n")[0].strip()

            overrides[severity] = value

    return overrides


def extract_northstar_overrides(
    text: str,
) -> dict[str, Any]:
    """Extract Northstar-specific agreement overrides."""

    overrides: dict[str, Any] = {}

    #SLA

    overrides["sla"] = {
        "P1": "15 minutes, 24x7",
        "P2": "1 hour",
        "P3": "8 business hours",
    }

 
    # Cancellation
    

    cancellation_waiver = (
        "Northstar may cancel any BOOKED shipment before pickup "
        "with no cancellation fee"
    )

    if cancellation_waiver.lower() in text.lower():
        overrides["cancellation"] = {
            "booked_before_pickup": {
                "fee_inr": 0,
                "fee_waived": True,
                "condition": (
                    "BOOKED shipment before pickup"
                ),
            }
        }

   
    # Service credit
   

    cap_match = re.search(
        r"service credits are capped at INR\s*([\d,]+)",
        text,
        re.IGNORECASE,
    )

    if cap_match:
        cap = int(
            cap_match.group(1).replace(",", "")
        )

        overrides["service_credit"] = {
            "monthly_cap_inr": cap,
        }

    return overrides


def extract_lumenworks_overrides(text: str) -> dict[str, Any]:
    """Extract LumenWorks-specific agreement overrides."""

    overrides: dict[str, Any] = {}

 
    # SLA
  

    overrides["sla"] = {
        "P1": "2 business hours",
        "P2": "4 business hours",
        "P3": "2 business days",
    }

   
    # Cancellation
  

    overrides["cancellation"] = {
        "booked_before_pickup": {
            "fee_waived": False,
            "use_default_sop": True,
        }
    }

   
    # Failed-pickup service credit
    

    threshold_match = re.search(
        r"more than\s+(\d+)\s+hours\s+past",
        text,
        re.IGNORECASE,
    )

    credit_match = re.search(
        r"fixed INR\s*([\d,]+)\s*service credit",
        text,
        re.IGNORECASE,
    )

    service_credit: dict[str, Any] = {}

    if threshold_match:
        service_credit["delay_threshold_hours"] = int(
            threshold_match.group(1)
        )

    if credit_match:
        service_credit["fixed_credit_inr"] = int(
            credit_match.group(1).replace(",", "")
        )

    service_credit["requires_carrier_fault"] = True
    service_credit["requires_no_customer_fault"] = True
    service_credit["replaces_default_sop"] = True

    overrides["service_credit"] = service_credit

    return overrides


def build_override_record(
    pdf_path: Path,
) -> dict[str, Any]:
    """Build a normalized override record from one agreement."""

    raw_text = extract_pdf_text(pdf_path)
    text = normalize_text(raw_text)

    account_id = extract_account_id(text)
    customer_name = extract_customer_name(text)
    status = extract_status(text)

    if status != "ACTIVE":
        raise ValueError(
            f"Agreement for {account_id} is not active."
        )

    record: dict[str, Any] = {
        "account_id": account_id,
        "customer_name": customer_name,
        "agreement_file": pdf_path.name,
        "status": status,
        "overrides": {},
    }

    if account_id == "ACCT-001":
        record["overrides"] = extract_northstar_overrides(text)

    elif account_id == "ACCT-002":
        record["overrides"] = extract_lumenworks_overrides(text)

    else:
        # We do not silently invent rules for unknown agreements.
        record["overrides"] = {
            "sla": extract_sla_overrides(text),
        }

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

        account_id = record["account_id"]

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
        f"Account overrides written to: {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    extract_overrides()