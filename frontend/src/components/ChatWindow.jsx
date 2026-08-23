import { useState } from "react";

import { useChat } from "../hooks/useChat";

import ActionConfirmation from "./ActionConfirmation";
import ActivityTimeline from "./ActivityTimeline";
import EmptyState from "./EmptyState";
import MessageBubble from "./MessageBubble";


function ChatWindow({ userId }) {
  const [input, setInput] =
    useState("");


  const {
    messages,
    events,
    isStreaming,
    error,
    pendingAction,
    sendMessage,
    stopStreaming,
    clearPendingAction,
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


  const handleActionComplete =
    (result) => {
      clearPendingAction();

      /*
       * We will add the execution result
       * to the conversation in the next
       * refinement.
       */
      console.log(
        "Action completed:",
        result
      );
    };


  const hasMessages =
    messages.length > 0;


  return (
    <section className="chat-layout">

      <div className="chat-content">

        {!hasMessages ? (
          <EmptyState />
        ) : (
          <div className="conversation">

            {messages.map(
              (message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                />
              )
            )}


            {error && (
              <div className="error-message">
                {error}
              </div>
            )}


            <ActivityTimeline
              events={events}
              isStreaming={
                isStreaming
              }
            />


            {pendingAction && (
              <ActionConfirmation
                action={pendingAction}
                userId={userId}
                onComplete={
                  handleActionComplete
                }
              />
            )}

          </div>
        )}

      </div>


      <div className="composer-container">

        <form
          className="composer"
          onSubmit={handleSubmit}
        >

          <textarea
            value={input}
            onChange={(event) =>
              setInput(
                event.target.value
              )
            }
            placeholder={
              "Ask about an order, SLA, cancellation..."
            }
            rows={1}
            disabled={isStreaming}
          />


          {isStreaming ? (
            <button
              type="button"
              className="composer-button stop"
              onClick={
                stopStreaming
              }
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              className="composer-button"
              disabled={
                !input.trim()
              }
            >
              Send
            </button>
          )}

        </form>


        <div className="composer-hint">
          ParcelPilot Support Assistant
        </div>

      </div>

    </section>
  );
}


export default ChatWindow;