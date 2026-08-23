
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

    # Read / deterministic tools
    READ_TOOLS = {
        "doc_search",
        "check_cancellation",
        "check_service_credit",
        "get_sla_target",
        "get_order_details",
    }

    # Only preview is available to the normal agent loop.
    # execute_action() should be called through the
    # explicit confirmation endpoint.
    ACTION_TOOLS = {
        "preview_action",
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

        This is not the authorization layer itself.
        It is the first guardrail before agent execution.
        """

  
        # Empty message
  
        if not user_message.strip():
            return GuardrailResult(
                allowed=False,
                reason="User message cannot be empty.",
            )

  
        # Role validation
  
        if context.role not in self.VALID_ROLES:
            return GuardrailResult(
                allowed=False,
                reason=(
                    f"Unsupported role: {context.role}"
                ),
            )


        # Request ID


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




    def check_pre_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        context: RequestContext,
    ) -> GuardrailResult:
        """
        Validate whether the authenticated identity is
        allowed to execute the requested tool.
        """

 
        # Tool authorization
 

        allowed_tools = (
            self.READ_TOOLS
            | self.ACTION_TOOLS
        )

        if tool_name not in allowed_tools:
            return GuardrailResult(
                allowed=False,
                reason=(
                    f"Unknown or unauthorized tool: "
                    f"{tool_name}"
                ),
            )


        # Action authorization


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


        # CUSTOMER-SPECIFIC SLA SCOPING
   

        if (
            context.role == "customer"
            and tool_name == "get_sla_target"
        ):
            requested_account = arguments.get(
                "account_id"
            )

            # If the model didn't provide an account,
            # force the authenticated account.
            if requested_account is None:

                arguments["account_id"] = (
                    context.account_id
                )

                # Customer cannot turn this into a
                # global plan-level query.
                arguments["plan"] = None

            # If the model provided an account, it must
            # match the authenticated account.
            elif (
                requested_account
                != context.account_id
            ):
                logger.warning(
                    "SLA account-scope violation | "
                    "request_id=%s | "
                    "context_account=%s | "
                    "requested_account=%s",
                    context.request_id,
                    context.account_id,
                    requested_account,
                )

                return GuardrailResult(
                    allowed=False,
                    reason=(
                        "Customer SLA queries must use "
                        "the authenticated account."
                    ),
                )


        # GENERAL CUSTOMER ACCOUNT SCOPING


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
                    "Account-scope violation | "
                    "request_id=%s | "
                    "role=%s | "
                    "context_account=%s | "
                    "requested_account=%s | "
                    "tool=%s",
                    context.request_id,
                    context.role,
                    context.account_id,
                    requested_account_id,
                    tool_name,
                )

                return GuardrailResult(
                    allowed=False,
                    reason=(
                        "Customer is not authorized "
                        "to access another account."
                    ),
                )


        # CUSTOMER DOCUMENT SEARCH
 

        if (
            context.role == "customer"
            and tool_name == "doc_search"
        ):
            requested_account = arguments.get(
                "account_id"
            )

            # Force authenticated account scope.
            if requested_account is None:

                arguments["account_id"] = (
                    context.account_id
                )

            # Reject attempts to search another
            # customer's documents.
            elif (
                requested_account
                != context.account_id
            ):
                logger.warning(
                    "Document-search account violation | "
                    "request_id=%s | "
                    "context_account=%s | "
                    "requested_account=%s",
                    context.request_id,
                    context.account_id,
                    requested_account,
                )

                return GuardrailResult(
                    allowed=False,
                    reason=(
                        "Customer document searches "
                        "must use the authenticated account."
                    ),
                )


        # DEPRECATED DOCUMENT RETRIEVAL


        if (
            tool_name == "doc_search"
            and arguments.get(
                "include_deprecated",
                False,
            )
        ):
            logger.info(
                "Deprecated document retrieval requested | "
                "request_id=%s",
                context.request_id,
            )

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
            "Pre-tool guardrail passed | "
            "request_id=%s | "
            "tool=%s | "
            "role=%s",
            context.request_id,
            tool_name,
            context.role,
        )

        return GuardrailResult(
            allowed=True
        )


    # ACCOUNT RESOLUTION


    def _resolve_tool_account_id(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> str | None:
        """
        Resolve the account associated with a tool call.
        """

   
        # Direct account-based tools
    

        if tool_name == "get_sla_target":
            return arguments.get("account_id")

        if tool_name == "doc_search":
            return arguments.get("account_id")

        # Order-based tools
  

        if tool_name in {
            "check_cancellation",
            "check_service_credit",
            "get_order_details",
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


        # Action tools


        if tool_name == "preview_action":
            return arguments.get("account_id")

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
        Validate that a tool result is safe to pass
        back to the agent.
        """

        # Normalize result


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

     
        # Source/status information
    

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


 

        if (
            isinstance(source, str)
            and "DEPRECATED"
            in source.upper()
        ):
            logger.warning(
                "Deprecated source blocked | "
                "request_id=%s | "
                "tool=%s | source=%s",
                context.request_id,
                tool_name,
                source,
            )

            return GuardrailResult(
                allowed=False,
                reason=(
                    "Tool result references a "
                    "deprecated source."
                ),
            )

        logger.info(
            "Post-tool guardrail passed | "
            "request_id=%s | "
            "tool=%s | "
            "source=%s",
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
        Validate the final response before returning it
        to the user.
        """


        # Empty response
  

        if not answer.strip():
            return GuardrailResult(
                allowed=False,
                reason=(
                    "Agent produced an empty answer."
                ),
            )

 
        # Tool-backed responses need evidence
 

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
            "Output guardrail passed | "
            "request_id=%s",
            context.request_id,
        )

        return GuardrailResult(
            allowed=True,
            metadata={
                "sources": tool_results,
            },
        )