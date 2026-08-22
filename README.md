parcelpilot-agent/
│
├── src/
│   ├── backend/
│   │   ├── main.py
│   │   └── routes/
│   │       ├── chat.py
│   │       ├── actions.py
│   │       └── health.py
│   │
│   ├── agent/
│   │   ├── loop.py
│   │   ├── guardrails.py
│   │   └── tool_defs.py
│   │
│   ├── tools/
│   │   ├── doc_search.py
│   │   ├── structured_data.py
│   │   └── actions.py
│   │
│   ├── ingestion/
│   │   ├── build_doc_index.py
│   │   ├── extract_overrides.py
│   │   └── load_xlsx.py
│   │
│   ├── data/
│   │   ├── parcelpilot.db
│   │   ├── account_overrides.json
│   │   └── chroma/
│   │
│   ├── logging/
│   │   └── logger.py
│   │
│   └── config/
│       └── settings.py
│
├── tests/
│   ├── test_cancellation.py
│   ├── test_service_credit.py
│   └── test_regression.py
│
├── docs/
├── frontend/
├── .env
├── .gitignore
├── requirements.txt
└── README.md

## database schema
parcelpilot.db
│
├── dataset_metadata
├── accounts
├── orders
└── tickets

### realationship
accounts
   │
   ├──────────< orders
   │
   └──────────< tickets
### schemas
parcelpilot.db

dataset_metadata
----------------
key PK
value


accounts
----------------
account_id PK
account_name
plan
status
csm
contract_file
premium_support
notes


orders
----------------
order_id PK
account_id FK → accounts
carrier
status
booked_at
pickup_window_start
pickup_window_end
pickup_actual_at
shipment_fee_inr
carrier_fault
customer_fault
cancellation_requested_at
notes


tickets
----------------
ticket_id PK
account_id FK → accounts
created_at
status
subject
description
channel
assigned_to
last_customer_message_at
historical_resolution

## running tests
    python -m pytest tests/test_structured_data.py -v