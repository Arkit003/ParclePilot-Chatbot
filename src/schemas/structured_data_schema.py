

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel, Field



@dataclass
class CancellationResult:
    order_id: str
    account_id: str
    status: str

    allowed: bool
    cancellation_fee_inr: int

    reason: str
    source: str

    requires_confirmation: bool = False
    requires_manager_approval: bool = False


@dataclass
class ServiceCreditResult:
    order_id: str
    account_id: str

    eligible: bool
    credit_amount_inr: int

    reason: str
    source: str

    requires_manager_approval: bool = False

class GetSLATargetInput(BaseModel):
    account_id: str | None = Field(
        default=None,
        description=(
            "ParcelPilot account ID. Use this when the question "
            "is about a specific customer account."
        ),
    )

    plan: str | None = Field(
        default=None,
        description=(
            "ParcelPilot plan. Use this for plan-level default "
            "SLA questions."
        ),
    )

    severity: str | None = Field(
        default=None,
        description=(
            "Severity P1, P2, or P3. Omit this to return "
            "the complete P1/P2/P3 SLA matrix."
        ),
    )
from pydantic import BaseModel


class SLATargetResult(BaseModel):
    account_id: str | None = None
    plan: str
    severity: str | None = None
    target: str | None = None
    targets: dict[str, str] | None = None
    source: str

class OrderDetailsResult(BaseModel):
    order_id: str
    account_id: str
    status: str
    customer_name: str | None = None
    shipment_fee_inr: float | None = None
    booked_at: str | None = None
    pickup_window_start: str | None = None
    pickup_window_end: str | None = None
    delivered_at: str | None = None
    source: str = "Customer Service Agreement"