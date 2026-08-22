from __future__ import annotations

from pathlib import Path
from typing import TypedDict


BASE_DIR = Path(__file__).resolve().parents[2]
DOCS_DIR = BASE_DIR / "docs"


class DocumentMetadata(TypedDict, total=False):
    filename: str
    document_type: str
    status: str
    version: str
    effective_date: str
    account_id: str | None
    customer_name: str | None


DOCUMENT_MANIFEST: list[DocumentMetadata] = [
    {
        "filename": "01_Support_Policy_v3_CURRENT.pdf",
        "document_type": "support_policy",
        "status": "CURRENT",
        "version": "v3",
        "effective_date": "2026-05-01",
        "account_id": None,
        "customer_name": None,
    },
    {
        "filename": "02_Support_Policy_v2_DEPRECATED.pdf",
        "document_type": "support_policy",
        "status": "DEPRECATED",
        "version": "v2",
        "effective_date": "2025-01-01",
        "account_id": None,
        "customer_name": None,
    },
    {
        "filename": "03_Cancellation_and_Service_Credit_SOP_v4.pdf",
        "document_type": "sop",
        "status": "CURRENT",
        "version": "v4",
        "effective_date": "2026-06-15",
        "account_id": None,
        "customer_name": None,
    },
    {
        "filename": "04_Product_Operations_Guide_and_Known_Issues.pdf",
        "document_type": "product_documentation",
        "status": "CURRENT",
        "version": None,
        "effective_date": "2026-08-14",
        "account_id": None,
        "customer_name": None,
    },
    {
        "filename": "05_Northstar_Logistics_Enterprise_Agreement.pdf",
        "document_type": "customer_agreement",
        "status": "ACTIVE",
        "version": None,
        "effective_date": "2026-01-01",
        "account_id": "ACCT-001",
        "customer_name": "Northstar Logistics",
    },
    {
        "filename": "06_LumenWorks_Service_Agreement.pdf",
        "document_type": "customer_agreement",
        "status": "ACTIVE",
        "version": None,
        "effective_date": "2026-03-01",
        "account_id": "ACCT-002",
        "customer_name": "LumenWorks",
    },
]


def get_document_path(metadata: DocumentMetadata) -> Path:
    """Return the absolute path for a manifest document."""

    path = DOCS_DIR / metadata["filename"]

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {path}"
        )

    return path