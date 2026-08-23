# src/agent/loop.py

from __future__ import annotations

import json
import logging
from typing import Any

from src.agent.guardrails import (
    GuardrailEngine,
    GuardrailViolation,
    RequestContext,
)
from src.agent.tool_defs import TOOL_DEFINITIONS
from src.agent.tool_registry import TOOL_REGISTRY
from src.agent.prompt import SYSTEM_PROMPT


logger = logging.getLogger(__name__)

MAX_ITERATIONS = 5


class AgentLoop:
    """
    ReAct-style agent loop.

    Flow:

        User
          ↓
        Input guardrail
          ↓
        LLM
          ↓
        Tool call
          ↓
        Pre-tool guardrail
          ↓
        Tool execution
          ↓
        Post-tool guardrail
          ↓
        LLM
          ↓
        ...
          ↓
        Output guardrail
          ↓
        Final answer

    The loop is independent of the underlying LLM provider.
    """

    def __init__(
        self,
        llm_client: Any,
        model: str,
        guardrails: GuardrailEngine | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.model = model
        self.guardrails = guardrails or GuardrailEngine()

    def run(
        self,
        messages: list[dict[str, Any]],
        context: RequestContext,
    ) -> str:
        """
        Execute the agent loop.

        Parameters
        ----------
        messages:
            Initial conversation messages.

        context:
            Authenticated request context containing:
            user_id, role, account_id, request_id.

        Returns
        -------
        str
            Final validated assistant response.
        """

        if not messages:
            raise ValueError(
                "Agent requires at least one message."
            )

        conversation = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *messages,
        ]

        
        # 1. INPUT GUARDRAIL
      

        user_message = conversation[-1].get(
            "content",
            "",
        )

        input_check = self.guardrails.check_input(
            user_message=user_message,
            context=context,
        )

        if not input_check.allowed:
            logger.warning(
                "Input guardrail blocked request | "
                "request_id=%s | reason=%s",
                context.request_id,
                input_check.reason,
            )

            raise GuardrailViolation(
                input_check.reason
            )

        # Keep successful tool results so the final
        # output guardrail can verify that the response
        # has traceable evidence.
        tool_results: list[dict[str, Any]] = []

     
        # 2. AGENT LOOP
        

        for iteration in range(
            1,
            MAX_ITERATIONS + 1,
        ):
            logger.info(
                "Agent iteration started | "
                "request_id=%s | iteration=%d",
                context.request_id,
                iteration,
            )

         
            # LLM CALL
         

            try:
                response = (
                    self.llm_client
                    .chat.completions.create(
                        model=self.model,
                        messages=conversation,
                        tools=TOOL_DEFINITIONS,
                        tool_choice="auto",
                    )
                )

            except Exception as exc:
                logger.exception(
                    "LLM call failed | "
                    "request_id=%s | iteration=%d",
                    context.request_id,
                    iteration,
                )

                return (
                    "I couldn't process the request right now. "
                    "Please try again."
                )

            if not response.choices:
                logger.error(
                    "LLM returned no choices | "
                    "request_id=%s",
                    context.request_id,
                )

                return (
                    "I couldn't generate a response. "
                    "Please try again."
                )

            assistant_message = (
                response.choices[0].message
            )

       
            # Convert assistant message to a normal dict
     

            assistant_dict: dict[str, Any] = {
                "role": "assistant",
                "content": (
                    assistant_message.content
                ),
            }

            if assistant_message.tool_calls:

                assistant_dict["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": (
                                tool_call.function.name
                            ),
                            "arguments": (
                                tool_call.function.arguments
                            ),
                        },
                    }
                    for tool_call
                    in assistant_message.tool_calls
                ]

            conversation.append(
                assistant_dict
            )

  
            # 3. NO TOOL CALL → FINAL ANSWER
  

            if not assistant_message.tool_calls:

                answer = (
                    assistant_message.content
                    or ""
                )

                logger.info(
                    "LLM produced final answer | "
                    "request_id=%s | iteration=%d",
                    context.request_id,
                    iteration,
                )

                # OUTPUT GUARDRAIL
  

                output_check = (
                    self.guardrails.check_output(
                        answer=answer,
                        context=context,
                        tool_results=tool_results,
                    )
                )

                if not output_check.allowed:
                    logger.warning(
                        "Output guardrail blocked response | "
                        "request_id=%s | reason=%s",
                        context.request_id,
                        output_check.reason,
                    )

                    return (
                        "I couldn't safely verify the answer. "
                        "Please contact support for assistance."
                    )

                return answer


            # 4. PROCESS TOOL CALLS


            for tool_call in (
                assistant_message.tool_calls
            ):

                tool_name = (
                    tool_call.function.name
                )

                raw_arguments = (
                    tool_call.function.arguments
                )

                logger.info(
                    "Tool requested | "
                    "request_id=%s | tool=%s",
                    context.request_id,
                    tool_name,
                )

                # Parse JSON arguments


                try:
                    arguments = json.loads(
                        raw_arguments
                    )

                except json.JSONDecodeError:

                    logger.warning(
                        "Invalid tool arguments | "
                        "request_id=%s | tool=%s",
                        context.request_id,
                        tool_name,
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.id
                            ),
                            "content": json.dumps(
                                {
                                    "error": (
                                        "Tool arguments "
                                        "were not valid JSON."
                                    )
                                }
                            ),
                        }
                    )

                    continue


                # Validate arguments are an object


                if not isinstance(
                    arguments,
                    dict,
                ):

                    logger.warning(
                        "Tool arguments were not an object | "
                        "request_id=%s | tool=%s",
                        context.request_id,
                        tool_name,
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.id
                            ),
                            "content": json.dumps(
                                {
                                    "error": (
                                        "Tool arguments "
                                        "must be a JSON object."
                                    )
                                }
                            ),
                        }
                    )

                    continue


                # Check tool exists


                tool = TOOL_REGISTRY.get(
                    tool_name
                )

                if tool is None:

                    logger.warning(
                        "Unknown tool requested | "
                        "request_id=%s | tool=%s",
                        context.request_id,
                        tool_name,
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.id
                            ),
                            "content": json.dumps(
                                {
                                    "error": (
                                        f"Unknown tool: "
                                        f"{tool_name}"
                                    )
                                }
                            ),
                        }
                    )

                    continue

                # 5. PRE-TOOL GUARDRAIL


                pre_tool = (
                    self.guardrails.check_pre_tool(
                        tool_name=tool_name,
                        arguments=arguments,
                        context=context,
                    )
                )

                if not pre_tool.allowed:

                    logger.warning(
                        "Pre-tool guardrail blocked tool | "
                        "request_id=%s | tool=%s | reason=%s",
                        context.request_id,
                        tool_name,
                        pre_tool.reason,
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.id
                            ),
                            "content": json.dumps(
                                {
                                    "error": (
                                        pre_tool.reason
                                    )
                                }
                            ),
                        }
                    )

                    continue

                if tool_name in {
                    "check_cancellation",
                    "check_service_credit",
                }:
                    arguments["request_time"] = (
                        context.dataset_snapshot
                    )
                # 6. EXECUTE TOOL


                try:

                    tool_result = tool(
                        **arguments
                    )

                    logger.info(
                        "Tool execution completed | "
                        "request_id=%s | tool=%s",
                        context.request_id,
                        tool_name,
                    )

                except Exception as exc:

                    logger.exception(
                        "Tool execution failed | "
                        "request_id=%s | tool=%s",
                        context.request_id,
                        tool_name,
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.id
                            ),
                            "content": json.dumps(
                                {
                                    "error": str(exc)
                                }
                            ),
                        }
                    )

                    continue


                # Convert result to serializable dictionary


                if hasattr(
                    tool_result,
                    "model_dump",
                ):
                    result_data = (
                        tool_result.model_dump()
                    )

                elif hasattr(
                    tool_result,
                    "__dict__",
                ):
                    result_data = vars(
                        tool_result
                    )

                elif isinstance(
                    tool_result,
                    dict,
                ):
                    result_data = tool_result

                else:
                    result_data = {
                        "value": tool_result
                    }

                # 7. POST-TOOL GUARDRAIL


                post_tool = (
                    self.guardrails.check_post_tool(
                        tool_name=tool_name,
                        arguments=arguments,
                        result=tool_result,
                        context=context,
                    )
                )

                if not post_tool.allowed:

                    logger.warning(
                        "Post-tool guardrail blocked result | "
                        "request_id=%s | tool=%s | reason=%s",
                        context.request_id,
                        tool_name,
                        post_tool.reason,
                    )

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": (
                                tool_call.id
                            ),
                            "content": json.dumps(
                                {
                                    "error": (
                                        post_tool.reason
                                    )
                                }
                            ),
                        }
                    )

                    continue


                # Store successful tool trace


                tool_results.append(
                    {
                        "tool": tool_name,
                        "arguments": arguments,
                        "source": (
                            post_tool.metadata.get(
                                "source"
                            )
                        ),
                        "result": result_data,
                    }
                )


                # Send result back to LLM
  

                tool_content = json.dumps(
                    result_data,
                    default=str,
                )

                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": (
                            tool_call.id
                        ),
                        "content": tool_content,
                    }
                )

            logger.info(
                "Agent iteration completed | "
                "request_id=%s | iteration=%d",
                context.request_id,
                iteration,
            )

        # 8. ITERATION LIMIT
  

        logger.warning(
            "Agent iteration limit reached | "
            "request_id=%s | max_iterations=%d",
            context.request_id,
            MAX_ITERATIONS,
        )

        return (
            "I couldn't complete the request within the "
            "allowed reasoning steps. Please try simplifying "
            "the request or request human support."
        )