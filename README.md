# ParcelPilot Support Agent

An AI-powered support application for the ParcelPilot logistics platform.

The system combines an LLM with deterministic business tools, document retrieval, account-level authorization, and guardrails. The core idea is simple: the model decides what to look up, but it never decides who's allowed to see what or what a fee actually is. Those stay outside the model, in code.

It handles questions about orders, cancellations, service credits, SLA targets, customer agreements, and ParcelPilot's support documentation.

## Features

- Account-aware support conversations
- Multi-turn conversation context
- Deterministic tools for business-critical decisions
- Document retrieval using Chroma and BGE embeddings
- Customer-specific agreement overrides
- Role-based access control
- Pre-tool and post-tool guardrails
- Output evidence checks
- Streaming responses over Server-Sent Events
- Action preview and confirmation flow
- OpenRouter-compatible LLM integration
- Structured logging
- Mock authentication for local development

## Architecture

```
                         React Frontend
                              |
                              | HTTP / SSE
                              v
                         FastAPI Backend
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
      Agent Loop          Guardrails         Authentication
          |
          +--------------------+
          |                    |
          v                    v
      LLM Provider          Tool Registry
      (OpenRouter)               |
          |            +--------+---------+
          |            |        |         |
          |            v        v         v
          |       Order Tools  SLA     Document Search
          |                              |
          |                              v
          |                            Chroma
          |                              |
          |                              v
          |                       BGE Embeddings
          |
          v
     Final Response
```

The LLM decides which tool is useful and drafts the final response. The application owns everything else: authorization, account scoping, deterministic business rules, retrieval constraints, and any state-changing action.

## Project structure

```
parcelpilot/
├── src/
│   ├── agent/
│   │   ├── events.py
│   │   ├── guardrails.py
│   │   ├── loop.py
│   │   ├── prompt.py
│   │   ├── tool_defs.py
│   │   └── tool_registry.py
│   │
│   ├── backend/
│   │   ├── main.py
│   │   ├── auth.py
│   │   └── routes/
│   │
│   ├── database/
│   │   └── repositories/
│   │
│   ├── ingestion/
│   │
│   ├── logging/
│   │   └── logger.py
│   │
│   ├── schemas/
│   │
│   ├── tools/
│   │
│   └── llm/
│
├── data/
│   ├── chroma/
│   └── ...
│
├── tests/
│   ├── integration/
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   └── styles/
│   └── package.json
│
├── pyproject.toml
├── uv.lock
└── README.md
```

## Agent design

The agent runs a bounded tool-calling loop, not a free-running one.

```
User request
     |
     v
Input guardrail
     |
     v
    LLM
     |
     +---- no tool call ----> Output guardrail ----> Response
     |
     +---- tool call
              |
              v
        Pre-tool guardrail
              |
              v
          Tool execution
              |
              v
        Post-tool guardrail
              |
              v
             LLM
              |
             ...
              |
              v
        Output guardrail
              |
              v
         Final answer
```

The loop is capped at five iterations per request. That's a deliberate ceiling, not a default — it exists to stop uncontrolled tool execution, and the agent is expected to degrade gracefully (partial answer, ask for another turn) if it can't finish within that budget.

## Tools

- **get_order_details** — retrieves information about a specific order.
- **check_cancellation** — determines whether an order can be cancelled and what fee applies.
- **check_service_credit** — determines whether a shipment qualifies for a service credit.
- **get_sla_target** — returns the applicable SLA for an account or plan. Covers P1/P2/P3, account-specific overrides, plan-level defaults, and the full SLA matrix.
- **doc_search** — semantic search over ParcelPilot policies, agreements, and support documentation.
- **preview_action** — creates a pending action that requires explicit confirmation before it executes.

State-changing execution is deliberately kept outside the normal agent tool loop — see Actions and confirmation below.

## Guardrails

Guardrails enforce the constraints that should never be left to the LLM's judgment:

- authenticated user role
- customer account scope
- cross-account access prevention
- tool authorization
- document retrieval scope
- deprecated document handling
- tool-result validation
- final-answer evidence checks

For example: a customer authenticated for ACCT-001 cannot pull an order that belongs to ACCT-002, even if the model tries to request it. The model can propose an identifier. The application decides whether that identifier is actually accessible.

## Roles

Local development currently supports three roles:

- **customer** — tied to a single account.
- **support_agent** — internal user, not tied to one customer account.
- **manager** — internal user, approves actions above the SOP threshold.

## LLM provider

The app talks to the LLM through an OpenAI-compatible client abstraction, so the provider can be swapped without touching the agent loop. OpenRouter is the provider in use right now.

```
LLM_PROVIDER=openrouter

OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=your_model_here
```

The API key must never be committed to the repository.

## Document retrieval

Document search uses Chroma for vector storage, `BAAI/bge-small-en-v1.5` for embeddings, and metadata filters for account scoping and document status. The embedding model and Chroma client are initialized once at startup and reused across requests, rather than reloaded per search.

## Streaming

The backend exposes a streaming chat endpoint:

```
POST /chat/stream
```

It emits events the frontend can render live:

- `agent_started`
- `iteration_started`
- `tool_requested`
- `tool_completed`
- `guardrail_blocked`
- `action_preview`
- `final_answer`
- `agent_finished`
- `agent_error`

The frontend turns these into user-facing status text — "Checking order details...", "Checking cancellation eligibility...", "Cancellation eligibility checked." Internal model reasoning is never exposed to the user.

## Local development

### Backend

Create the environment and install dependencies with uv:

```
uv sync
source .venv/bin/activate
```

Set the required environment variables, then start the backend:

```
uvicorn src.backend.main:app --reload
```

The API is available at `http://localhost:8000`, with docs at `http://localhost:8000/docs`.

### Frontend

```
cd frontend
npm install
```

Create `frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

Then start the dev server:

```
npm run dev
```

The frontend is normally available at `http://localhost:5173`.

## Testing

Run the full backend suite:

```
python -m pytest -v
```

Run a single test file:

```
python -m pytest tests/test_structured_data.py -v
```

Run integration tests:

```
python -m pytest tests/integration -v
```

The suite covers deterministic tools, guardrails, authentication, tool definitions, agent behavior, document retrieval, and provider integration.

## Environment variables

Backend:

```
LLM_PROVIDER=openrouter

OPENROUTER_API_KEY=
OPENROUTER_MODEL=

FRONTEND_URL=http://localhost:5173
```

Frontend:

```
VITE_API_BASE_URL=http://localhost:8000
```


## Logging

Logging is handled by `src/logging/logger.py`. Logs are written to the application's log directory rather than printed inline by application code.

Events that get logged include: request IDs, agent iterations, tool calls, guardrail decisions, tool failures, LLM failures, action execution, and document searches.

## Actions and confirmation

State-changing operations go through a preview-confirm-execute flow, not a direct call:

```
Agent
  |
  v
preview_action
  |
  v
PENDING action
  |
  v
Frontend confirmation
  |
  +---- Cancel ----> CANCELLED
  |
  +---- Confirm
             |
             v
     /actions/{id}/execute
             |
             v
        authorization
             |
             v
          EXECUTED
```

`execute_action` is intentionally not exposed to the LLM as a normal tool — it's only reachable through the confirmation endpoint, after a human has approved the pending action.

## Conversation context

The frontend keeps the running conversation history and sends the relevant messages to the backend on each turn. The backend merges that history with trusted request context — authenticated role, authenticated account, request ID, dataset snapshot — so the model can follow up-questions like:

```
User: What is the P2 SLA for my account?
Assistant: ...
User: What about P1?
```

Conversation history gives the model continuity. Database lookups and guardrails remain the source of truth for authorization and business rules — the history is never trusted on its own for either.

## Account security

Account scope is enforced by the application, not inferred by the model.

Example: a customer authenticated as ACCT-001 asks about order ORD-2001. The database shows ORD-2001 belongs to ACCT-002. The request is blocked. The model can select an identifier, but the backend resolves it and checks access before anything is returned.

## Mock authentication

Local development uses a mock auth layer. Example users:

- `customer-northstar`
- `customer-lumenworks`
- `customer-beacon`
- `customer-axis`
- `rohit`, `maya` (support agents)
- `manager`

Customer users carry an associated account ID. Support agents and managers are internal users with no fixed customer account. This auth mechanism is for development and demonstration only — it is not production-ready.

## Deployment

Planned layout:

```
Vercel (React frontend)
        |
        v
Render (FastAPI backend)
        |
        v
OpenRouter
```

Frontend:

```
VITE_API_BASE_URL=https://your-render-service.onrender.com
```

Backend:

```
FRONTEND_URL=https://your-vercel-app.vercel.app
```

The OpenRouter API key stays on the backend and is never exposed to the browser.


## Persistence considerations

The current implementation uses local SQLite and Chroma persistence, which is fine for development and demo deployments but not durable production storage. Likely next steps if this grows past a demo:

- PostgreSQL instead of SQLite
- persistent or managed vector storage
- persistent conversation storage
- production authentication
- production secret management
- expanded action auditing

## Current status

Implemented and tested: deterministic business tools, account-aware guardrails, customer-specific agreement overrides, document retrieval, multi-turn conversation context, SSE streaming, OpenRouter integration, action preview and confirmation, and the React support interface.

Current focus: frontend refinement and deployment.

## License

Add the project's license information here once one has been selected.