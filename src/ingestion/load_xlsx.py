from __future__ import annotations
import sqlite3
from pathlib import Path
import pandas as pd



BASE_DIR = Path(__file__).resolve().parents[2]


XLSX_FILE = BASE_DIR / "docs" / "ParcelPilot_Assessment_Data.xlsx"

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = DATA_DIR / "parcelpilot.db"


#expected structures

EXPECTED_SHEETS = {
    "README",
    "accounts",
    "orders",
    "tickets",
}


EXPECTED_COLUMNS = {
    "accounts": [
        "account_id",
        "account_name",
        "plan",
        "status",
        "csm",
        "contract_file",
        "premium_support",
        "notes",
    ],
    "orders": [
        "order_id",
        "account_id",
        "carrier",
        "status",
        "booked_at",
        "pickup_window_start",
        "pickup_window_end",
        "pickup_actual_at",
        "shipment_fee_inr",
        "carrier_fault",
        "customer_fault",
        "cancellation_requested_at",
        "notes",
    ],
    "tickets": [
        "ticket_id",
        "account_id",
        "created_at",
        "status",
        "subject",
        "description",
        "channel",
        "assigned_to",
        "last_customer_message_at",
        "historical_resolution",
    ],
}


#helper functions

def validate_sheets(excel_file: Path) -> None:
    """Validate that the workbook contains the expected sheets."""

    available_sheets = set(pd.ExcelFile(excel_file).sheet_names)

    missing_sheets = EXPECTED_SHEETS - available_sheets

    if missing_sheets:
        raise ValueError(
            f"Missing required sheets: {sorted(missing_sheets)}"
        )


def validate_columns(
    dataframe: pd.DataFrame,
    sheet_name: str,
) -> None:
    """Validate required columns for a given sheet."""

    expected = EXPECTED_COLUMNS[sheet_name]
    actual = list(dataframe.columns)

    missing_columns = set(expected) - set(actual)

    if missing_columns:
        raise ValueError(
            f"Sheet '{sheet_name}' is missing columns: "
            f"{sorted(missing_columns)}"
        )


def to_sqlite_bool(value) -> int:
    """
    Convert Excel/Pandas boolean-like values to SQLite 0/1.
    """

    if pd.isna(value):
        return 0

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, (int, float)):
        return int(bool(value))

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "yes", "1"}:
            return 1

        if normalized in {"false", "no", "0"}:
            return 0

    raise ValueError(
        f"Cannot convert value '{value}' to boolean."
    )


def clean_text(value) -> str | None:
    """
    Convert NaN/NaT to None.
    Preserve normal values as strings.
    """

    if pd.isna(value):
        return None

    return str(value).strip()


def clean_datetime(value) -> str | None:
    """
    Store workbook datetime values as ISO-like strings.

    SQLite does not have a native datetime type, so we store
    them as TEXT.
    """

    if pd.isna(value):
        return None

    timestamp = pd.Timestamp(value)

    return timestamp.strftime("%Y-%m-%d %H:%M")



#database creation


def create_tables(connection: sqlite3.Connection) -> None:
    

    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS dataset_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            account_name TEXT NOT NULL,
            plan TEXT NOT NULL,
            status TEXT NOT NULL,
            csm TEXT NOT NULL,
            contract_file TEXT,
            premium_support INTEGER NOT NULL DEFAULT 0,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            carrier TEXT NOT NULL,
            status TEXT NOT NULL,
            booked_at TEXT NOT NULL,
            pickup_window_start TEXT NOT NULL,
            pickup_window_end TEXT NOT NULL,
            pickup_actual_at TEXT,
            shipment_fee_inr REAL NOT NULL,
            carrier_fault INTEGER NOT NULL DEFAULT 0,
            customer_fault INTEGER NOT NULL DEFAULT 0,
            cancellation_requested_at TEXT,
            notes TEXT,

            FOREIGN KEY (account_id)
                REFERENCES accounts(account_id)
        );

        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            channel TEXT NOT NULL,
            assigned_to TEXT,
            last_customer_message_at TEXT,
            historical_resolution TEXT,

            FOREIGN KEY (account_id)
                REFERENCES accounts(account_id)
        );

        CREATE INDEX IF NOT EXISTS idx_orders_account_id
            ON orders(account_id);

        CREATE INDEX IF NOT EXISTS idx_orders_status
            ON orders(status);

        CREATE INDEX IF NOT EXISTS idx_tickets_account_id
            ON tickets(account_id);

        CREATE INDEX IF NOT EXISTS idx_tickets_status
            ON tickets(status);

        CREATE INDEX IF NOT EXISTS idx_tickets_created_at
            ON tickets(created_at);
        """
    )


#inserting metadata

def insert_metadata(
    connection: sqlite3.Connection,
    snapshot_time: str,
) -> None:
    """Insert dataset-level metadata."""

    connection.execute(
        """
        INSERT INTO dataset_metadata (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        ("dataset_snapshot", snapshot_time),
    )

    connection.execute(
        """
        INSERT INTO dataset_metadata (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        ("currency", "INR"),
    )


#insert accounts


def insert_accounts(
    connection: sqlite3.Connection,
    dataframe: pd.DataFrame,
) -> None:
    """Insert account records."""

    records = []

    for _, row in dataframe.iterrows():
        records.append(
            (
                clean_text(row["account_id"]),
                clean_text(row["account_name"]),
                clean_text(row["plan"]),
                clean_text(row["status"]),
                clean_text(row["csm"]),
                clean_text(row["contract_file"]),
                to_sqlite_bool(row["premium_support"]),
                clean_text(row["notes"]),
            )
        )

    connection.executemany(
        """
        INSERT INTO accounts (
            account_id,
            account_name,
            plan,
            status,
            csm,
            contract_file,
            premium_support,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )



# Insert orders



def insert_orders(
    connection: sqlite3.Connection,
    dataframe: pd.DataFrame,
) -> None:
    """Insert order records."""

    records = []

    for _, row in dataframe.iterrows():
        shipment_fee = row["shipment_fee_inr"]

        if pd.isna(shipment_fee):
            raise ValueError(
                f"Missing shipment fee for order "
                f"{row['order_id']}"
            )

        records.append(
            (
                clean_text(row["order_id"]),
                clean_text(row["account_id"]),
                clean_text(row["carrier"]),
                clean_text(row["status"]),
                clean_datetime(row["booked_at"]),
                clean_datetime(row["pickup_window_start"]),
                clean_datetime(row["pickup_window_end"]),
                clean_datetime(row["pickup_actual_at"]),
                float(shipment_fee),
                to_sqlite_bool(row["carrier_fault"]),
                to_sqlite_bool(row["customer_fault"]),
                clean_datetime(row["cancellation_requested_at"]),
                clean_text(row["notes"]),
            )
        )

    connection.executemany(
        """
        INSERT INTO orders (
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )



# Insert tickets

def insert_tickets(
    connection: sqlite3.Connection,
    dataframe: pd.DataFrame,
) -> None:
    """Insert ticket records."""

    records = []

    for _, row in dataframe.iterrows():
        records.append(
            (
                clean_text(row["ticket_id"]),
                clean_text(row["account_id"]),
                clean_datetime(row["created_at"]),
                clean_text(row["status"]),
                clean_text(row["subject"]),
                clean_text(row["description"]),
                clean_text(row["channel"]),
                clean_text(row["assigned_to"]),
                clean_datetime(row["last_customer_message_at"]),
                clean_text(row["historical_resolution"]),
            )
        )

    connection.executemany(
        """
        INSERT INTO tickets (
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
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        records,
    )



# main ingestion


def load_xlsx(
    excel_file: Path = XLSX_FILE,
    db_file: Path = DB_FILE,
) -> None:
    """
    Load the ParcelPilot Excel workbook into SQLite.

    The operation is transactional. If anything fails,
    the database changes are rolled back.
    """

    if not excel_file.exists():
        raise FileNotFoundError(
            f"Workbook not found: {excel_file}"
        )

    print(f"Loading workbook: {excel_file}")

    # Read workbook
    workbook = pd.ExcelFile(excel_file)

    available_sheets = set(workbook.sheet_names)

    missing_sheets = EXPECTED_SHEETS - available_sheets

    if missing_sheets:
        raise ValueError(
            f"Missing required sheets: {sorted(missing_sheets)}"
        )

    # Read individual sheets
    readme_df = pd.read_excel(
        workbook,
        sheet_name="README",
    )

    accounts_df = pd.read_excel(
        workbook,
        sheet_name="accounts",
    )

    orders_df = pd.read_excel(
        workbook,
        sheet_name="orders",
    )

    tickets_df = pd.read_excel(
        workbook,
        sheet_name="tickets",
    )

    # Validate schemas
    validate_columns(accounts_df, "accounts")
    validate_columns(orders_df, "orders")
    validate_columns(tickets_df, "tickets")

    # README contains dataset snapshot metadata.
    # The workbook currently has a single snapshot value.
    snapshot_time = str(readme_df.iloc[0, 1]).strip()

    # Start fresh for deterministic ingestion.
    if db_file.exists():
        db_file.unlink()

    db_file.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_file)

    try:
        # Enforce FK constraints.
        connection.execute("PRAGMA foreign_keys = ON")

        # Create schema.
        create_tables(connection)

        # Insert data.
        insert_metadata(
            connection,
            snapshot_time,
        )

        insert_accounts(
            connection,
            accounts_df,
        )

        insert_orders(
            connection,
            orders_df,
        )

        insert_tickets(
            connection,
            tickets_df,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    print(f"Database created successfully: {db_file}")



if __name__ == "__main__":
    load_xlsx()