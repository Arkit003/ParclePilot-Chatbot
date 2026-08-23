from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.database.database import Database
from src.database.repositories.accounts import AccountRepository
from src.database.repositories.orders import OrderRepository


logger = logging.getLogger(__name__)



# Identity / request context


@dataclass(frozen=True)
class RequestContext:
    user_id: str
    role: str
    account_id: str | None
    request_id: str
    dataset_snapshot: str



# Guardrail result



@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class GuardrailViolation(Exception):
    """Raised when a guardrail blocks an operation."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)



# Guardrail engine


class GuardrailEngine:

    VALID_ROLES = {
        "customer",
        "support_agent",
        "manager",
    }

    READ_TOOLS = {
        "doc_search",
        "check_cancellation",
        "check_service_credit",
        "get_sla_target",
    }

    ACTION_TOOLS = {
    "preview_action",
    "execute_action",
}

    def __init__(self) -> None:
        database = Database()

        self.account_repository = AccountRepository(
            database
        )

        self.order_repository = OrderRepository(
            database
        )


    # 1. INPUT CHECK


    def check_input(
        self,
        user_message: str,
        context: RequestContext,
    ) -> GuardrailResult:
        """
        Basic request-level sanity checks.

        This is NOT a security system by itself.
        It is the first hook before agent execution.
        """

        if not user_message.strip():
            return GuardrailResult(
                allowed=False,
                reason="User message cannot be empty.",
            )

        if context.role not in self.VALID_ROLES:
            return GuardrailResult(
                allowed=False,
                reason=(
                    f"Unsupported role: {context.role}"
                ),
            )

        if not context.request_id.strip():
            return GuardrailResult(
                allowed=False,
                reason="Missing request ID.",
            )

        if context.role == "customer":
            if not context.account_id:
                return GuardrailResult(
                    allowed=False,
                    reason=(
                        "Customer requests require "
                        "an account context."
                    ),
                )

        logger.info(
            "Input guardrail passed | request_id=%s | "
            "role=%s | account_id=%s",
            context.request_id,
            context.role,
            context.account_id,
        )

        return GuardrailResult(
            allowed=True
        )


    # 2. PRE-TOOL CHECK
    

    def check_pre_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: RequestContext,
    ) -> GuardrailResult:
        """
        Validate whether this identity is allowed to
        execute the requested tool with these arguments.
        """

        if tool_name not in self.READ_TOOLS:
            return GuardrailResult(
                allowed=False,
                reason=f"Unknown or unauthorized tool: {tool_name}",
            )
        if (
            tool_name in self.ACTION_TOOLS
            and context.role
            not in {
                "support_agent",
                "manager",
            }
        ):
            return GuardrailResult(
                allowed=False,
                reason=(
                    "This role is not authorized "
                    "to perform support actions."
                ),
            )


        # Customer: enforce account scope


        if context.role == "customer":

            requested_account_id = (
                self._resolve_tool_account_id(
                    tool_name,
                    arguments,
                )
            )

            if (
                requested_account_id is not None
                and requested_account_id
                != context.account_id
            ):
                logger.warning(
                    "Account-scope violation | request_id=%s | "
                    "role=%s | context_account=%s | "
                    "requested_account=%s | tool=%s",
                    context.request_id,
                    context.role,
                    context.account_id,
                    requested_account_id,
                    tool_name,
                )

                return GuardrailResult(
                    allowed=False,
                    reason=(
                        "Customer is not authorized to "
                        "access another account."
                    ),
                )


        # Customer + doc_search


        if (
            context.role == "customer"
            and tool_name == "doc_search"
        ):
            requested_account = arguments.get(
                "account_id"
            )

            # The model doesn't get to choose a different
            # account. We enforce the authenticated account.
            if requested_account is None:
                arguments["account_id"] = (
                    context.account_id
                )

            elif requested_account != context.account_id:
                return GuardrailResult(
                    allowed=False,
                    reason=(
                        "Customer document searches "
                        "must use the authenticated account."
                    ),
                )


        # Deprecated retrieval


        if (
            tool_name == "doc_search"
            and arguments.get(
                "include_deprecated",
                False,
            )
        ):
            return GuardrailResult(
                allowed=True,
                reason=(
                    "Deprecated retrieval explicitly requested."
                ),
                metadata={
                    "historical_search": True,
                },
            )

        logger.info(
            "Pre-tool guardrail passed | request_id=%s | "
            "tool=%s | role=%s",
            context.request_id,
            tool_name,
            context.role,
        )

        return GuardrailResult(
            allowed=True
        )


    # Account resolution


    def _resolve_tool_account_id(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str | None:

        # Tools that directly specify an account.
        if tool_name == "get_sla_target":
            return arguments.get("account_id")

        if tool_name == "doc_search":
            return arguments.get("account_id")

        # Order-based tools need us to resolve
        # the account from the order.
        if tool_name in {
            "check_cancellation",
            "check_service_credit",
        }:
            order_id = arguments.get("order_id")

            if not order_id:
                return None

            order = (
                self.order_repository.get_by_id(
                    order_id
                )
            )

            if order is None:
                return None

            return order["account_id"]

        return None

 
    # 3. POST-TOOL CHECK


    def check_post_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        context: RequestContext,
    ) -> GuardrailResult:
        """
        Validate that the tool result is safe to pass
        back into the agent.
        """


        # Convert result into a dictionary where possible


        if hasattr(result, "model_dump"):
            result_data = result.model_dump()

        elif hasattr(result, "__dict__"):
            result_data = vars(result)

        elif isinstance(result, dict):
            result_data = result

        else:
            result_data = {
                "value": result
            }


        # Deprecated source protection


        status = result_data.get(
            "status"
        )

        source = result_data.get(
            "source"
        )

        if status == "DEPRECATED":
            logger.warning(
                "Deprecated tool result blocked | "
                "request_id=%s | tool=%s",
                context.request_id,
                tool_name,
            )

            return GuardrailResult(
                allowed=False,
                reason=(
                    "Tool produced a deprecated source."
                ),
            )

        # If the tool exposes source metadata as text,
        # reject clearly deprecated references.
        if (
            isinstance(source, str)
            and "DEPRECATED" in source.upper()
        ):
            return GuardrailResult(
                allowed=False,
                reason=(
                    "Tool result references a deprecated "
                    "source."
                ),
            )

        logger.info(
            "Post-tool guardrail passed | request_id=%s | "
            "tool=%s | source=%s",
            context.request_id,
            tool_name,
            source,
        )

        return GuardrailResult(
            allowed=True,
            metadata={
                "source": source,
                "result": result_data,
            },
        )


    # 4. OUTPUT CHECK


    def check_output(
        self,
        answer: str,
        context: RequestContext,
        tool_results: list[dict[str, Any]],
    ) -> GuardrailResult:
        """
        Validate the final answer before returning it.

        The first version focuses on:
        - non-empty response
        - no fabricated confidence markers
        - evidence presence for tool-backed answers
        """

        if not answer.strip():
            return GuardrailResult(
                allowed=False,
                reason="Agent produced an empty answer.",
            )

        # If tools were used, we expect some source
        # evidence to be available.
        if tool_results:

            sources = [
                result.get("source")
                for result in tool_results
                if result.get("source")
            ]

            if not sources:
                return GuardrailResult(
                    allowed=False,
                    reason=(
                        "Tool-backed response has no "
                        "traceable source."
                    ),
                )

        logger.info(
            "Output guardrail passed | request_id=%s",
            context.request_id,
        )

        return GuardrailResult(
            allowed=True,
            metadata={
                "sources": tool_results,
            },
        )