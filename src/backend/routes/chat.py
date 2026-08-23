from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from src.agent.guardrails import RequestContext
from src.agent.loop import AgentLoop
from src.backend.auth import build_request_context
from src.config import DATASET_SNAPSHOT
from src.llm.client import get_llm_client, get_model


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)


class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        description="User's support question.",
    )


class ChatResponse(BaseModel):
    answer: str
    request_id: str


@router.post(
    "",
    response_model=ChatResponse,
)
def chat(
    request: Request,
    body: ChatRequest,
) -> ChatResponse:

    try:
        user, request_id = build_request_context(
            request
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    context = RequestContext(
        user_id=user.user_id,
        role=user.role,
        account_id=user.account_id,
        request_id=request_id,
        dataset_snapshot=DATASET_SNAPSHOT,
    )

    logger.info(
        "Chat request received | "
        "request_id=%s | user_id=%s | role=%s | account_id=%s",
        request_id,
        user.user_id,
        user.role,
        user.account_id,
    )

    client = get_llm_client()
    model = get_model()

    agent = AgentLoop(
        llm_client=client,
        model=model,
    )

    answer = agent.run(
        messages=[
            {
                "role": "user",
                "content": body.message,
            }
        ],
        context=context,
    )

    return ChatResponse(
        answer=answer,
        request_id=request_id,
    )