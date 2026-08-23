import { useState } from "react";

import { useChat } from "../hooks/useChat";
import ToolCallEvent from "./ToolCallEvent";


function ChatWindow({ userId }) {
  const [input, setInput] =
    useState("");

  const {
    messages,
    events,
    isStreaming,
    error,
    sendMessage,
    stopStreaming,
  } = useChat(userId);


  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    const message =
      input.trim();

    if (
      !message ||
      isStreaming
    ) {
      return;
    }

    setInput("");

    await sendMessage(
      message
    );
  };


  return (
    <div className="chat-window">

      <div className="messages">
        {messages.map(
          (message) => (
            <div
              key={message.id}
              className={`message ${message.role}`}
            >
              {message.content}
            </div>
          )
        )}

        {error && (
          <div className="message system">
            {error}
          </div>
        )}
      </div>


      {events.length > 0 && (
        <div className="tool-events">
          {events.map(
            (event, index) => (
              <ToolCallEvent
                key={`${event.type}-${index}`}
                event={event}
              />
            )
          )}

          {isStreaming && (
            <div className="tool-event">
              <span>
                Working...
              </span>
            </div>
          )}
        </div>
      )}


      <form
        className="chat-input"
        onSubmit={handleSubmit}
      >
        <input
          value={input}
          onChange={(event) =>
            setInput(
              event.target.value
            )
          }
          placeholder={
            "Ask about shipments, SLAs, cancellations..."
          }
          disabled={isStreaming}
        />

        {isStreaming ? (
          <button
            type="button"
            onClick={
              stopStreaming
            }
          >
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={
              !input.trim()
            }
          >
            Send
          </button>
        )}
      </form>

    </div>
  );
}


export default ChatWindow;