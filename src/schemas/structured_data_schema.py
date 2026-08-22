

from __future__ import annotations

from dataclasses import dataclass





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


@dataclass
class SLATargetResult:
    account_id: str
    plan: str
    severity: str

    target: str
    source: str