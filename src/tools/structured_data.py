# TODO -we are hardcoding the accounts such as Norweign or Lumenworks 
        # but what if there are more such aggrements we need to handle that also

from __future__ import annotations
from typing import Optional
from datetime import datetime
from typing import Optional,Any

from src.database.database import Database
from src.database.repositories.accounts import AccountRepository
from src.database.repositories.orders import OrderRepository
from src.tools.schema import CancellationResult,ServiceCreditResult,SLATargetResult
from src.tools import (SLA_DEFAULTS,
                       DEFAULT_CANCELLATION_FEE,
                       DEFAULT_CANCELLATION_WINDOW_MINUTES,
                       DEFAULT_SERVICE_CREDIT_DELAY_HOURS,
                       DEFAULT_SERVICE_CREDIT_CAP,
                       DEFAULT_SERVICE_CREDIT_PERCENTAGE)
from src.config.overrides import OverrideStore
# loading out the data
database = Database()

account_repository = AccountRepository(database)
order_repository = OrderRepository(database)

override_store = OverrideStore()

#helpers
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
def get_agreement_source(
    account: dict[str, Any],
) -> str:
    agreement_file = account.get("agreement_file")

    if agreement_file:
        return agreement_file

    return "Customer Service Agreement"

#checking cancellation
def check_cancellation(order_id: str,request_time: str) -> CancellationResult:

    order = order_repository.get_by_id(order_id)

    if order is None:
        raise ValueError(
            f"Order not found: {order_id}"
        )

    account_id = order["account_id"]

    account = account_repository.get_by_id(
        account_id
    )

    if account is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    status = order["status"]

    booked_at = parse_datetime(
        order["booked_at"]
    )

    requested_at = parse_datetime(
        request_time
    )

    if booked_at is None:
        raise ValueError(
            f"Missing booking time for {order_id}"
        )

    if requested_at is None:
        raise ValueError(
            f"Missing request time for {order_id}"
        )

    agreement = override_store.get_account(
    account_id
    )

    overrides = agreement.get(
    "overrides",
    {}
    )

    agreement_source = get_agreement_source(
    agreement
    )

    cancellation_overrides = overrides.get(
        "cancellation",
        {},
    )


    # DRAFT

    if status == "DRAFT":
        return CancellationResult(
            order_id=order_id,
            account_id=account_id,
            status=status,
            allowed=True,
            cancellation_fee_inr=0,
            reason=(
                "Draft shipments may be cancelled "
                "without a fee."
            ),
            source="Cancellation & Service Credit SOP v4",
        )

    # PICKED_UP


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

   
    # DELIVERED
   

    if status == "DELIVERED":
        return CancellationResult(
            order_id=order_id,
            account_id=account_id,
            status=status,
            allowed=False,
            cancellation_fee_inr=0,
            reason=(
                "Delivered shipments cannot be cancelled."
            ),
            source="Cancellation & Service Credit SOP v4",
        )


    # BOOKED
  

    if status == "BOOKED":

        booked_before_pickup = (
            cancellation_overrides.get(
                "booked_before_pickup"
            )
        )

        # Agreement-specific override.
        if booked_before_pickup:
            fee_waived = booked_before_pickup.get(
                "fee_waived"
            )

            if fee_waived is True:
                return CancellationResult(
                    order_id=order_id,
                    account_id=account_id,
                    status=status,
                    allowed=True,
                    cancellation_fee_inr=0,
                    reason=(
                        "The customer's agreement waives "
                        "the cancellation fee for BOOKED "
                        "shipments before pickup."
                    ),
                    source=(
                        agreement_source
                    ),
                )

        minutes_since_booking = (
            requested_at - booked_at
        ).total_seconds() / 60

        if minutes_since_booking <= (
            DEFAULT_CANCELLATION_WINDOW_MINUTES
        ):
            return CancellationResult(
                order_id=order_id,
                account_id=account_id,
                status=status,
                allowed=True,
                cancellation_fee_inr=0,
                reason=(
                    "The shipment was cancelled within "
                    "30 minutes of booking."
                ),
                source=(
                    "Cancellation & Service Credit SOP v4"
                ),
            )

        # Default SOP fee applies.
        return CancellationResult(
            order_id=order_id,
            account_id=account_id,
            status=status,
            allowed=True,
            cancellation_fee_inr=(
                DEFAULT_CANCELLATION_FEE
            ),
            reason=(
                "The shipment was booked more than "
                "30 minutes ago and no cancellation "
                "fee waiver applies."
            ),
            source=(
                "Cancellation & Service Credit SOP v4"
            ),
        )

    raise ValueError(
        f"Unsupported order status: {status}"
    )


#Checking serivice credit
def check_service_credit(
    order_id: str,
    request_time: str,
) -> ServiceCreditResult:

    order = order_repository.get_by_id(
        order_id
    )

    if order is None:
        raise ValueError(
            f"Order not found: {order_id}"
        )

    account_id = order["account_id"]

    account = account_repository.get_by_id(
        account_id
    )

    if account is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    pickup_window_end = parse_datetime(
        order["pickup_window_end"]
    )

    request_dt = parse_datetime(
        request_time
    )

    if pickup_window_end is None:
        raise ValueError(
            f"Missing pickup window end for {order_id}"
        )

    if request_dt is None:
        raise ValueError(
            f"Missing request time for {order_id}"
        )

    carrier_fault = bool(
        order["carrier_fault"]
    )

    customer_fault = bool(
        order["customer_fault"]
    )

    # The SOP explicitly says not to promise a
    # credit when fault is unknown or customer fault exists.
    if not carrier_fault or customer_fault:
        return ServiceCreditResult(
            order_id=order_id,
            account_id=account_id,
            eligible=False,
            credit_amount_inr=0,
            reason=(
                "Service credit cannot be granted because "
                "carrier fault is not established or "
                "customer fault exists."
            ),
            source=(
                "Cancellation & Service Credit SOP v4"
            ),
        )

    delay_hours = (
        request_dt - pickup_window_end
    ).total_seconds() / 3600

    agreement = override_store.get_account(
    account_id
    )

    overrides = agreement.get(
    "overrides",
    {}
    )

    agreement_source = get_agreement_source(
    agreement
    )

    service_credit_overrides = overrides.get(
        "service_credit",
        {},
    )

   
    # Agreement-specific threshold
 

    threshold_hours = service_credit_overrides.get(
        "delay_threshold_hours",
        DEFAULT_SERVICE_CREDIT_DELAY_HOURS,
    )

    if delay_hours <= threshold_hours:
        return ServiceCreditResult(
            order_id=order_id,
            account_id=account_id,
            eligible=False,
            credit_amount_inr=0,
            reason=(
                f"Pickup is not more than "
                f"{threshold_hours} hours late."
            ),
            source=(
                agreement_source
                if "delay_threshold_hours"
                in service_credit_overrides
                else "Cancellation & Service Credit SOP v4"
            ),
        )

   
    # Fixed agreement credit
    

    fixed_credit = service_credit_overrides.get(
        "fixed_credit_inr"
    )

    if fixed_credit is not None:

        credit = int(fixed_credit)

        monthly_cap = service_credit_overrides.get(
            "monthly_cap_inr"
        )

        if monthly_cap is not None:
            # We don't yet have historical monthly
            # aggregate credit information available
            # in the current orders schema.
            #
            # Therefore the cap cannot be verified here.
            # The result should carry that uncertainty.
            pass

        return ServiceCreditResult(
            order_id=order_id,
            account_id=account_id,
            eligible=True,
            credit_amount_inr=credit,
            reason=(
                "The customer agreement defines a "
                "fixed service-credit amount."
            ),
            source=agreement_source,
            requires_manager_approval=(
                credit > 1000
            ),
        )


    # Default SOP calculation
   

    shipment_fee = float(
        order["shipment_fee_inr"]
    )

    percentage_credit = (
        shipment_fee
        * DEFAULT_SERVICE_CREDIT_PERCENTAGE
    )

    credit = min(
        DEFAULT_SERVICE_CREDIT_CAP,
        int(percentage_credit),
    )

    return ServiceCreditResult(
        order_id=order_id,
        account_id=account_id,
        eligible=True,
        credit_amount_inr=credit,
        reason=(
            "Default service-credit conditions "
            "are satisfied."
        ),
        source=(
            "Cancellation & Service Credit SOP v4"
        ),
        requires_manager_approval=(
            credit > 1000
        ),
    )


# SLA targets

def get_sla_target(account_id: str,severity: str) -> SLATargetResult:

    account = account_repository.get_by_id(
        account_id
    )

    if account is None:
        raise ValueError(
            f"Account not found: {account_id}"
        )

    if severity not in {
        "P1",
        "P2",
        "P3",
    }:
        raise ValueError(
            f"Unsupported severity: {severity}"
        )

    plan = account["plan"]

    agreement = override_store.get_account(
    account_id
    )

    overrides = agreement.get(
    "overrides",
    {}
    )

    agreement_source = get_agreement_source(
    agreement
    )

    sla_overrides = overrides.get(
        "sla",
        {},
    )

    if severity in sla_overrides:
        return SLATargetResult(
            account_id=account_id,
            plan=plan,
            severity=severity,
            target=sla_overrides[severity],
            source=agreement_source,
        )

    plan_targets = SLA_DEFAULTS.get(
        plan
    )

    if plan_targets is None:
        raise ValueError(
            f"Unsupported plan: {plan}"
        )

    return SLATargetResult(
        account_id=account_id,
        plan=plan,
        severity=severity,
        target=plan_targets[severity],
        source="ParcelPilot Support Policy v3",
    )