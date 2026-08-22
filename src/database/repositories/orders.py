from __future__ import annotations

from src.database.database import Database


class OrderRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_by_id(self, order_id: str):
        return self.database.fetch_one(
            """
            SELECT
                order_id,
                account_id,
                carrier,
                status,
                booked_at,
                pickup_window_start,
                pickup_window_end,
                pickup_actual_at,
                shipment_fee_inr,
                carrier_fault,
                customer_fault,
                cancellation_requested_at,
                notes
            FROM orders
            WHERE order_id = ?
            """,
            (order_id,),
        )