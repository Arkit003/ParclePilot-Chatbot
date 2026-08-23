from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.routes.chat import router as chat_router
from src.backend.routes.health import router as health_router
from src.backend.routes.stream import router as stream_router
from src.logging.logger import setup_logging
from src.agent.tool_registry import initialize_tools
from src.tools.doc_search import create_search_engine,DocumentSearch


setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "Initializing document search engine."
    )

    search_engine = create_search_engine()

    app.state.search_engine = search_engine

    initialize_tools(
        search_engine
    )

    logger.info(
        "Document search engine initialized."
    )

    yield

    logger.info(
        "ParcelPilot backend shutting down."
    )
def create_search_engine() -> DocumentSearch:
    return DocumentSearch()

app = FastAPI(
    title="ParcelPilot Support Agent",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
)

app.include_router(
    chat_router,
)

app.include_router(
    stream_router,
)


@app.on_event("startup")
def startup() -> None:
    logger.info(
        "ParcelPilot backend started"
    )