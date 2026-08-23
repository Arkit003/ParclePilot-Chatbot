from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentSearchInput(BaseModel):
    query: str = Field(
        min_length=1,
    )

    account_id: str | None = None

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    include_deprecated: bool = False

class DocumentSearchResult(BaseModel):
    content: str
    document_name: str
    document_type: str
    status: str
    version: str | None = None
    effective_date: str
    account_id: str | None = None
    customer_name: str | None = None
    score: float