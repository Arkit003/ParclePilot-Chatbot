from src.tools.actions import preview_action
from src.tools.doc_search import (
    DocumentSearch,
    doc_search,
)
from src.tools.structured_data import (
    check_cancellation,
    check_service_credit,
    get_order_details,
    get_sla_target,
)


TOOL_REGISTRY = {
    "doc_search": doc_search,
    "check_cancellation": check_cancellation,
    "check_service_credit": check_service_credit,
    "get_order_details": get_order_details,
    "get_sla_target": get_sla_target,
    "preview_action": preview_action,
}


# def initialize_tools(
#     search_engine: DocumentSearch,
# ) -> None:
#     TOOL_REGISTRY["doc_search"] = (
#         lambda **kwargs: doc_search(
#             search_engine=search_engine,
#             **kwargs,
#         )
#     )