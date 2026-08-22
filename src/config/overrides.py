from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[2]
OVERRIDES_FILE = BASE_DIR / "data" / "account_overrides.json"


class OverrideStore:
    """Loads and provides access to account-specific agreement overrides."""

    def __init__(self, file_path: Path = OVERRIDES_FILE) -> None:
        self.file_path = file_path
        self._overrides: dict[str, Any] | None = None

    def load(self) -> None:
        """Load the override file into memory."""

        if not self.file_path.exists():
            raise FileNotFoundError(
                f"Override file not found: {self.file_path}"
            )

        with self.file_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError(
                "account_overrides.json must contain a JSON object."
            )

        self._overrides = data

    def get_account_overrides(
        self,
        account_id: str,
    ) -> dict[str, Any]:
        """Return overrides for an account."""

        if self._overrides is None:
            self.load()

        assert self._overrides is not None

        account = self._overrides.get(account_id)

        if account is None:
            return {}

        return account.get("overrides", {})
    
    def get_account(self,account_id: str,) -> dict[str, Any]:
        """Return the complete agreement record for an account."""

        if self._overrides is None:
            self.load()

        assert self._overrides is not None

        account = self._overrides.get(account_id)

        if account is None:
            return {}

        return account

    def reload(self) -> None:
        """Force a reload from disk."""

        self._overrides = None
        self.load()