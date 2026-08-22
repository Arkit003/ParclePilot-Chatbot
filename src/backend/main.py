import logging
from fastapi import FastAPI
from src.logging.logger import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

logger.info("ParcelPilot application started")

app = FastAPI(
    title="ParcelPilot Support Agent",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    logger.info("Health check requested")
    return {"status": "ok"}