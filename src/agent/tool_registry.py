from __future__ import annotations

from typing import Any, Callable

from src.tools.doc_search import doc_search
from src.tools.structured_data import (
    check_cancellation,
    check_service_credit,
    get_sla_target,
)


TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "doc_search": doc_search,
    "check_cancellation": check_cancellation,
    "check_service_credit": check_service_credit,
    "get_sla_target": get_sla_target,
}