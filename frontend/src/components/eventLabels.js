export function getEventLabel(event) {
  switch (event.type) {
    case "agent_started":
      return "Starting support review...";

    case "iteration_started":
      return `Reviewing request...`;

    case "tool_requested":
      return getToolRequestedLabel(
        event.data?.tool
      );

    case "tool_completed":
      return getToolCompletedLabel(
        event.data?.tool
      );

    case "guardrail_blocked":
      return "Request blocked by access policy.";

    case "final_answer":
      return null;

    case "agent_finished":
      return null;

    case "agent_error":
      return "Something went wrong while processing the request.";

    default:
      return null;
  }
}


function getToolRequestedLabel(tool) {
  switch (tool) {
    case "check_cancellation":
      return "Checking cancellation eligibility...";

    case "check_service_credit":
      return "Checking service-credit eligibility...";

    case "get_sla_target":
      return "Checking SLA policy...";

    case "doc_search":
      return "Checking ParcelPilot documentation...";

    case "preview_action":
      return "Preparing the requested action...";

    default:
      return "Checking support information...";
  }
}


function getToolCompletedLabel(tool) {
  switch (tool) {
    case "check_cancellation":
      return "Cancellation eligibility checked.";

    case "check_service_credit":
      return "Service-credit eligibility checked.";

    case "get_sla_target":
      return "SLA policy checked.";

    case "doc_search":
      return "Relevant documentation checked.";

    case "preview_action":
      return "Action preview prepared.";

    default:
      return "Support check completed.";
  }
}