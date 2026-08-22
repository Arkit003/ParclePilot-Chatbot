from __future__ import annotations

from src.database.database import Database


class TicketRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_by_id(self, ticket_id: str):
        return self.database.fetch_one(
            """
            SELECT
                ticket_id,
                account_id,
                created_at,
                status,
                subject,
                description,
                channel,
                assigned_to,
                last_customer_message_at,
                historical_resolution
            FROM tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        )