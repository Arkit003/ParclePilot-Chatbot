function cleanMarkdown(text) {
  if (!text) {
    return "";
  }

  return text
    // Bold: **text** -> text
    .replace(/\*\*(.*?)\*\*/g, "$1")
    // Italic: *text* -> text
    .replace(/(?<!\*)\*(?!\*)(.*?)\*(?!\*)/g, "$1");
}


function MessageBubble({ message }) {
  const content =
    cleanMarkdown(message.content);

  return (
    <div
      className={`message-row ${message.role}`}
    >
      <div className="message-bubble">

        {message.role === "assistant" && (
          <div className="assistant-label">
            ParcelPilot Assistant
          </div>
        )}

        <div className="message-content">
          {content}
        </div>

      </div>
    </div>
  );
}

export default MessageBubble;