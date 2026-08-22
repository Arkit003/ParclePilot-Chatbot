from __future__ import annotations

from pydantic import BaseModel, Field


class DocumentSearchInput(BaseModel):
    query: str = Field(
        min_length=1,
        description="Natural-language search query.",
    )

    account_id: str | None = Field(
        default=None,
        description=(
            "Account to scope customer-specific documents to."
        ),
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of results to return.",
    )

    include_deprecated: bool = Field(
        default=False,
        description=(
            "Whether explicitly requested historical/deprecated "
            "documents may be returned."
        ),
    )

class DocumentSearchResult(BaseModel):
    content: str
    document_name: str
    document_type: str
    status: str
    version: str | None
    effective_date: str
    account_id: str | None
    customer_name: str | None
    score: float