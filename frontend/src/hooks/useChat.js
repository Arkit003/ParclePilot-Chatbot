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

  const abortControllerRef =
    useRef(null);


  const sendMessage = useCallback(
  async (message) => {
    const trimmed = message.trim();

    if (!trimmed || isStreaming) {
      return;
    }

    setError(null);
    setEvents([]);
    setIsStreaming(true);

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: trimmed,
    };

    // IMPORTANT:
    // Capture the history BEFORE setMessages because
    // React state updates are asynchronous.
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
          setEvents((current) => [
            ...current,
            event,
          ]);

          if (
            event.type ===
            "final_answer"
          ) {
            const answer =
              event.data?.answer ?? "";

            setMessages((current) => [
              ...current,
              {
                id: crypto.randomUUID(),
                role: "assistant",
                content: answer,
              },
            ]);
          }
        },
      });
    } catch (err) {
      if (err?.name !== "AbortError") {
        setError(
          err instanceof Error
            ? err.message
            : "Something went wrong."
        );
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  },
  [
    isStreaming,
    userId,
    messages,
  ]
);


  const stopStreaming = useCallback(
    () => {
      abortControllerRef.current?.abort();
      setIsStreaming(false);
    },
    []
  );


  const clearConversation =
    useCallback(() => {
      setMessages([]);
      setEvents([]);
      setError(null);
    }, []);


  return {
    messages,
    events,
    isStreaming,
    error,
    sendMessage,
    stopStreaming,
    clearConversation,
  };
}