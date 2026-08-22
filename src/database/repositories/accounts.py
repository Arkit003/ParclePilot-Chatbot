from __future__ import annotations
from src.database.database import Database


class AccountRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def get_by_id(self, account_id: str):
        return self.database.fetch_one(
            """
            SELECT
                account_id,
                account_name,
                plan,
                status,
                csm,
                contract_file,
                premium_support,
                notes
            FROM accounts
            WHERE account_id = ?
            """,
            (account_id,),
        )