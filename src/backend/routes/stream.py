from __future__ import annotations

import asyncio
import json
import logging
import threading
from queue import Empty, Queue

from fastapi import APIRouter, Request,HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agent.events import AgentEvent
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


class StreamChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
    )


def format_sse(
    event: AgentEvent,
) -> str:
    """
    Convert an AgentEvent into an SSE message.

    SSE format:

        event: <event type>
        data: <JSON>

    followed by a blank line.
    """

    return (
        f"event: {event.type}\n"
        f"data: {json.dumps(event.data, default=str)}\n\n"
    )


@router.post("/stream")
async def chat_stream(
    request: Request,
    body: StreamChatRequest,
):
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

    event_queue: Queue[AgentEvent | None] = Queue()

    def emit(event: AgentEvent) -> None:
        event_queue.put(event)

    def run_agent() -> None:
        try:
            client = get_llm_client()
            model = get_model()

            agent = AgentLoop(
                llm_client=client,
                model=model,
                event_callback=emit,
            )

            agent.run(
                messages=[
                    {
                        "role": "user",
                        "content": body.message,
                    }
                ],
                context=context,
            )

        except Exception as exc:
            logger.exception(
                "Streaming agent failed | request_id=%s",
                request_id,
            )

            emit(
                AgentEvent(
                    type="agent_error",
                    data={
                        "request_id": request_id,
                        "error": str(exc),
                    },
                )
            )

        finally:
            event_queue.put(None)

    thread = threading.Thread(
        target=run_agent,
        daemon=True,
    )

    thread.start()

    async def event_generator():
        while True:
            try:
                event = await asyncio.to_thread(
                    event_queue.get,
                )

            except asyncio.CancelledError:
                logger.info(
                    "SSE client disconnected | request_id=%s",
                    request_id,
                )
                break

            if event is None:
                break

            yield format_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Request-ID": request_id,
        },
    )