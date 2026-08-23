import { useState } from "react";

import { streamChat } from "../api/chat";
import ToolCallEvent from "./ToolCallEvent";


function ChatWindow({ userId }) {
  const [input, setInput] = useState("");
  const [messages, setMessages] =
    useState([]);

  const [events, setEvents] = useState(
    []
  );

  const [loading, setLoading] =
    useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    const message = input.trim();

    if (!message || loading) {
      return;
    }

    setInput("");
    setLoading(true);
    setEvents([]);

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: message,
      },
    ]);

    await streamChat({
      message,
      userId,

      onEvent: (agentEvent) => {
        setEvents((current) => [
          ...current,
          agentEvent,
        ]);

        if (
          agentEvent.type ===
          "final_answer"
        ) {
          setMessages((current) => [
            ...current,
            {
              role: "assistant",
              content:
                agentEvent.data
                  .answer ?? "",
            },
          ]);
        }
      },

      onError: (error) => {
        setMessages((current) => [
          ...current,
          {
            role: "system",
            content:
              error.message ??
              "Something went wrong.",
          },
        ]);
      },

      onDone: () => {
        setLoading(false);
      },
    });
  };

  return (
    <div className="chat-window">
      <div className="messages">
        {messages.map(
          (message, index) => (
            <div
              key={index}
              className={`message ${message.role}`}
            >
              {message.content}
            </div>
          )
        )}
      </div>

      <div className="tool-events">
        {events.map(
          (event, index) => (
            <ToolCallEvent
              key={`${event.type}-${index}`}
              event={event}
            />
          )
        )}
      </div>

      <form
        className="chat-input"
        onSubmit={handleSubmit}
      >
        <input
          value={input}
          onChange={(event) =>
            setInput(event.target.value)
          }
          placeholder="Ask ParcelPilot..."
          disabled={loading}
        />

        <button
          type="submit"
          disabled={
            loading ||
            !input.trim()
          }
        >
          {loading
            ? "Thinking..."
            : "Send"}
        </button>
      </form>
    </div>
  );
}

export default ChatWindow;