import { getEventLabel } from "./eventLabels";


function ToolCallEvent({ event }) {
  const label =
    getEventLabel(event);

  if (!label) {
    return null;
  }

  const isWarning =
    event.type ===
    "guardrail_blocked";

  const isComplete =
    event.type ===
    "tool_completed";

  return (
    <div
      className={`tool-event ${
        isWarning
          ? "warning"
          : isComplete
            ? "success"
            : ""
      }`}
    >
      <span className="tool-event-indicator">
        {isWarning
          ? "!"
          : isComplete
            ? "✓"
            : "•"}
      </span>

      <span>{label}</span>
    </div>
  );
}


export default ToolCallEvent;