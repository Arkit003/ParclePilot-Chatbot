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