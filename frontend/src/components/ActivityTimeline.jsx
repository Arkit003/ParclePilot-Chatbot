import { getEventLabel } from "./eventLabels";


function ActivityTimeline({
  events,
  isStreaming,
}) {
  const visibleEvents =
    events
      .map((event) => ({
        event,
        label: getEventLabel(event),
      }))
      .filter(
        ({ label }) => label
      );

  if (!visibleEvents.length) {
    return null;
  }

  return (
    <div className="activity-card">

      <div className="activity-title">
        Support activity
      </div>

      <div className="activity-list">

        {visibleEvents.map(
          ({ event, label }, index) => {

            const completed =
              event.type ===
              "tool_completed";

            const warning =
              event.type ===
              "guardrail_blocked";

            return (
              <div
                key={`${event.type}-${index}`}
                className={`activity-item ${
                  warning
                    ? "warning"
                    : completed
                      ? "completed"
                      : ""
                }`}
              >
                <div className="activity-dot">
                  {warning
                    ? "!"
                    : completed
                      ? "✓"
                      : ""}
                </div>

                <span>
                  {label}
                </span>
              </div>
            );
          }
        )}

        {isStreaming && (
          <div className="activity-item">
            <div className="activity-dot loading" />
            <span>
              Working...
            </span>
          </div>
        )}

      </div>

    </div>
  );
}

export default ActivityTimeline;