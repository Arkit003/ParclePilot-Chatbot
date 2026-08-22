from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "parcelpilot.db"


class Database:
    """Small wrapper around the ParcelPilot SQLite database."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        """
        Create a new SQLite connection.

        A new connection is created for each operation rather than
        keeping one global connection alive.
        """
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Database not found: {self.db_path}"
            )

        connection = sqlite3.connect(self.db_path)

        # Return rows that can be accessed by column name.
        connection.row_factory = sqlite3.Row

        # Explicitly enable FK enforcement.
        connection.execute("PRAGMA foreign_keys = ON")

        return connection

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> sqlite3.Row | None:
        """Execute a SELECT query and return one row."""

        with self.connect() as connection:
            return connection.execute(
                query,
                params,
            ).fetchone()

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> list[sqlite3.Row]:
        """Execute a SELECT query and return all rows."""

        with self.connect() as connection:
            return connection.execute(
                query,
                params,
            ).fetchall()

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] = (),
    ) -> None:
        """Execute a write operation."""

        with self.connect() as connection:
            connection.execute(query, params)
            connection.commit()