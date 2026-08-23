import {
  useCallback,
  useRef,
  useState,
} from "react";

import { streamChat } from "../api/chat";


export function useChat(userId) {
  const [messages, setMessages] =
    useState([]);

  const [events, setEvents] =
    useState([]);

  const [isStreaming, setIsStreaming] =
    useState(false);

  const [error, setError] =
    useState(null);

  const [pendingAction, setPendingAction] =
    useState(null);

  const abortControllerRef =
    useRef(null);


  const sendMessage = useCallback(
    async (message) => {
      const trimmed =
        message.trim();

      if (
        !trimmed ||
        isStreaming
      ) {
        return;
      }

      setError(null);
      setEvents([]);
      setPendingAction(null);
      setIsStreaming(true);

      const userMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
      };

      /*
       * React state updates are asynchronous.
       * Build the conversation before updating state.
       */
      const conversation = [
        ...messages,
        userMessage,
      ];

      setMessages(conversation);

      const controller =
        new AbortController();

      abortControllerRef.current =
        controller;

      try {
        await streamChat({
          messages: conversation.map(
            (message) => ({
              role: message.role,
              content: message.content,
            })
          ),

          userId,

          signal: controller.signal,

          onEvent: (event) => {
            /*
             * Keep SSE events for the activity timeline.
             */
            setEvents((current) => [
              ...current,
              event,
            ]);


            /*
             * Agent created a pending action.
             */
            if (
              event.type ===
              "action_preview"
            ) {
              setPendingAction({
                confirmationId:
                  event.data
                    ?.confirmation_id,

                actionType:
                  event.data
                    ?.action_type,

                accountId:
                  event.data
                    ?.account_id,

                amountInr:
                  event.data
                    ?.amount_inr,

                reason:
                  event.data
                    ?.reason,

                status:
                  event.data
                    ?.status,
              });
            }


            /*
             * Final assistant response.
             */
            if (
              event.type ===
              "final_answer"
            ) {
              const answer =
                event.data
                  ?.answer ?? "";

              setMessages((current) => [
                ...current,
                {
                  id: crypto.randomUUID(),
                  role: "assistant",
                  content: answer,
                },
              ]);
            }


            /*
             * Backend agent error.
             */
            if (
              event.type ===
              "agent_error"
            ) {
              setError(
                event.data
                  ?.error ??
                  "The support agent encountered an error."
              );
            }
          },
        });
      } catch (err) {
        if (
          err?.name !==
          "AbortError"
        ) {
          setError(
            err instanceof Error
              ? err.message
              : "Something went wrong."
          );
        }
      } finally {
        setIsStreaming(false);

        abortControllerRef.current =
          null;
      }
    },
    [
      isStreaming,
      userId,
      messages,
    ]
  );


  const stopStreaming =
    useCallback(() => {
      abortControllerRef.current?.abort();

      abortControllerRef.current =
        null;

      setIsStreaming(false);
    }, []);


  const clearConversation =
    useCallback(() => {
      abortControllerRef.current?.abort();

      abortControllerRef.current =
        null;

      setMessages([]);
      setEvents([]);
      setPendingAction(null);
      setError(null);
      setIsStreaming(false);
    }, []);


  const clearPendingAction =
    useCallback(() => {
      setPendingAction(null);
    }, []);


  return {
    messages,
    events,
    isStreaming,
    error,
    pendingAction,
    sendMessage,
    stopStreaming,
    clearConversation,
    clearPendingAction,
  };
}