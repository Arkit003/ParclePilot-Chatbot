from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.routes.chat import router as chat_router
from src.backend.routes.health import router as health_router
from src.backend.routes.stream import router as stream_router
from src.logging.logger import setup_logging


setup_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ParcelPilot Support Agent",
    version="0.1.0",
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