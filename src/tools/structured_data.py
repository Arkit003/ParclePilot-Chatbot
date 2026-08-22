# TODO -we are hardcoding the accounts such as Norweign or Lumenworks 
        # but what if there are more such aggrements we need to handle that also

from __future__ import annotations
from typing import Optional
from datetime import datetime
from typing import Optional

from src.database.database import Database
from src.database.repositories.accounts import AccountRepository
from src.database.repositories.orders import OrderRepository
from src.tools.schema import CancellationResult,ServiceCreditResult,SLATargetResult
from src.tools import SLA_DEFAULTS
# loading out the data
database = Database()

account_repository = AccountRepository(database)
order_repository = OrderRepository(database)

#datetime helper
def parse_datetime(value: str | None) -> Optional[datetime]:
    """
    used to parse the datetime from the text
    """
    if value is None:
        return None

    return datetime.strptime(
        value,
        "%Y-%m-%d %H:%M",
    )

def check_cancellation(
    order_id: str,
    request_time: str,
) -> CancellationResult:

    order = order_repository.get_by_id(order_id)

    if order is None:
        raise ValueError(
            f"Order not found: {order_id}"
        )

    account_id = order["account_id"]

    account = account_repository.get_by_id(account_id)

    if account is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    status = order["status"]
    booked_at = parse_datetime(order["booked_at"])
    requested_at = parse_datetime(request_time)

    if booked_at is None or requested_at is None:
        raise ValueError(
            f"Missing cancellation timing data for {order_id}"
        )

    #chekcing draft shipment

    if status == "DRAFT":
        return CancellationResult(
            order_id=order_id,
            account_id=account_id,
            status=status,
            allowed=True,
            cancellation_fee_inr=0,
            reason="Draft shipments may be cancelled without a fee.",
            source="Cancellation & Service Credit SOP v4",
        )

    #picked up

    if status == "PICKED_UP":
        return CancellationResult(
            order_id=order_id,
            account_id=account_id,
            status=status,
            allowed=False,
            cancellation_fee_inr=0,
            reason=(
                "Shipment has already been picked up. "
                "Use the return-to-origin workflow."
            ),
            source="Cancellation & Service Credit SOP v4",
        )

    
    # if delivered
   

    if status == "DELIVERED":
        return CancellationResult(
            order_id=order_id,
            account_id=account_id,
            status=status,
            allowed=False,
            cancellation_fee_inr=0,
            reason="Delivered shipments cannot be cancelled.",
            source="Cancellation & Service Credit SOP v4",
        )

    
    # if just booked

    if status == "BOOKED":

        contract_file = account["contract_file"]

        # Northstar-specific override.
        if account_id == "ACCT-001":
            return CancellationResult(
                order_id=order_id,
                account_id=account_id,
                status=status,
                allowed=True,
                cancellation_fee_inr=0,
                reason=(
                    "Northstar may cancel any BOOKED shipment "
                    "before pickup without a cancellation fee."
                ),
                source="Northstar Logistics Enterprise Agreement",
            )

        minutes_since_booking = (
            requested_at - booked_at
        ).total_seconds() / 60

        if minutes_since_booking <= 30:
            return CancellationResult(
                order_id=order_id,
                account_id=account_id,
                status=status,
                allowed=True,
                cancellation_fee_inr=0,
                reason=(
                    "BOOKED shipments may be cancelled without "
                    "a fee within 30 minutes of booking."
                ),
                source="Cancellation & Service Credit SOP v4",
            )

        return CancellationResult(
            order_id=order_id,
            account_id=account_id,
            status=status,
            allowed=True,
            cancellation_fee_inr=250,
            reason=(
                "The shipment was booked more than 30 minutes ago "
                "and no agreement-specific cancellation waiver applies."
            ),
            source="Cancellation & Service Credit SOP v4",
        )

    raise ValueError(
        f"Unsupported order status: {status}"
    )

#Checking serivice credit
def check_service_credit(
    order_id: str,
    request_time: str,
) -> ServiceCreditResult:

    order = order_repository.get_by_id(order_id)

    if order is None:
        raise ValueError(
            f"Order not found: {order_id}"
        )

    account_id = order["account_id"]

    account = account_repository.get_by_id(account_id)

    if account is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    pickup_window_end = parse_datetime(
        order["pickup_window_end"]
    )

    if pickup_window_end is None:
        raise ValueError(
            f"Missing pickup window end for {order_id}"
        )

    request_dt = parse_datetime(request_time)

    if request_dt is None:
        raise ValueError(
            f"Missing request time for {order_id}"
        )

    # Carrier/customer fault must be known.
    carrier_fault = bool(order["carrier_fault"])
    customer_fault = bool(order["customer_fault"])

    if not carrier_fault or customer_fault:
        return ServiceCreditResult(
            order_id=order_id,
            account_id=account_id,
            eligible=False,
            credit_amount_inr=0,
            reason=(
                "Service credit cannot be granted because "
                "carrier fault is not established or customer fault exists."
            ),
            source="Cancellation & Service Credit SOP v4",
        )

    delay_hours = (
        request_dt - pickup_window_end
    ).total_seconds() / 3600

    # LumenWorks override.
    if account_id == "ACCT-002":

        if delay_hours <= 4:
            return ServiceCreditResult(
                order_id=order_id,
                account_id=account_id,
                eligible=False,
                credit_amount_inr=0,
                reason=(
                    "LumenWorks becomes eligible only when pickup "
                    "is more than 4 hours late."
                ),
                source="LumenWorks Service Agreement",
            )

        return ServiceCreditResult(
            order_id=order_id,
            account_id=account_id,
            eligible=True,
            credit_amount_inr=300,
            reason=(
                "LumenWorks receives a fixed ₹300 credit when "
                "the pickup is more than 4 hours late and the carrier "
                "is at fault."
            ),
            source="LumenWorks Service Agreement",
        )

    # Default SOP
    if delay_hours <= 2:
        return ServiceCreditResult(
            order_id=order_id,
            account_id=account_id,
            eligible=False,
            credit_amount_inr=0,
            reason=(
                "Pickup is not more than 2 hours past "
                "the scheduled pickup window."
            ),
            source="Cancellation & Service Credit SOP v4",
        )

    shipment_fee = float(order["shipment_fee_inr"])

    credit = min(
        500,
        int(shipment_fee * 0.10),
    )

    return ServiceCreditResult(
        order_id=order_id,
        account_id=account_id,
        eligible=True,
        credit_amount_inr=credit,
        reason=(
            "Default service-credit conditions are satisfied."
        ),
        source="Cancellation & Service Credit SOP v4",
        requires_manager_approval=credit > 1000,
    )


# SLA targets

def get_sla_target(account_id: str,severity: str,) -> SLATargetResult:

    account = account_repository.get_by_id(account_id)

    if account is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    plan = account["plan"]

    if plan not in SLA_DEFAULTS:
        raise ValueError(
            f"Unsupported plan: {plan}"
        )

    if severity not in {"P1", "P2", "P3"}:
        raise ValueError(
            f"Unsupported severity: {severity}"
        )

    # Northstar override.
    if account_id == "ACCT-001":
        override = {
            "P1": "15 minutes, 24x7",
            "P2": "1 hour",
            "P3": "8 business hours",
        }

        return SLATargetResult(
            account_id=account_id,
            plan=plan,
            severity=severity,
            target=override[severity],
            source="Northstar Logistics Enterprise Agreement",
        )

    return SLATargetResult(
        account_id=account_id,
        plan=plan,
        severity=severity,
        target=SLA_DEFAULTS[plan][severity],
        source="ParcelPilot Support Policy v3",
    )