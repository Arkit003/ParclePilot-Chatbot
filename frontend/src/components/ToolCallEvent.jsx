function ToolCallEvent({ event }) {
  const {
    tool,
    arguments: args,
    iteration,
    stage,
    reason,
  } = event.data;

  if (event.type === "tool_requested") {
    return (
      <div className="tool-event">
        <strong>🔧 {tool}</strong>
        <span>
          Running tool
          {iteration
            ? ` (iteration ${iteration})`
            : ""}
        </span>
      </div>
    );
  }

  if (event.type === "tool_completed") {
    return (
      <div className="tool-event success">
        <strong>✅ {tool}</strong>
        <span>Completed</span>
      </div>
    );
  }

  if (event.type === "guardrail_blocked") {
    return (
      <div className="tool-event warning">
        <strong>🛡️ Guardrail blocked</strong>
        <span>
          {tool}
          {stage ? ` · ${stage}` : ""}
          {reason ? ` · ${reason}` : ""}
        </span>
      </div>
    );
  }

  if (event.type === "iteration_started") {
    return (
      <div className="tool-event">
        <span>
          🔄 Reasoning step{" "}
          {iteration}
        </span>
      </div>
    );
  }

  return null;
}

export default ToolCallEvent;