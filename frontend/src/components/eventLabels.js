export function getEventLabel(event) {
  switch (event.type) {
    case "agent_started":
      return "Starting support review...";

    case "iteration_started":
      return null;

    case "tool_requested":
      return toolRequestedLabel(
        event.data?.tool
      );

    case "tool_completed":
      return toolCompletedLabel(
        event.data?.tool
      );

    case "guardrail_blocked":
      return "Access policy check blocked this request.";

    case "agent_error":
      return "A support operation encountered an error.";

    default:
      return null;
  }
}


function toolRequestedLabel(tool) {
  switch (tool) {
    case "check_cancellation":
      return "Checking cancellation eligibility...";

    case "check_service_credit":
      return "Checking service-credit eligibility...";

    case "get_sla_target":
      return "Checking SLA policy...";

    case "get_order_details":
      return "Checking order details...";

    case "doc_search":
      return "Checking ParcelPilot documentation...";

    case "preview_action":
      return "Preparing the requested action...";

    default:
      return "Checking support information...";
  }
}


function toolCompletedLabel(tool) {
  switch (tool) {
    case "check_cancellation":
      return "Cancellation eligibility checked.";

    case "check_service_credit":
      return "Service-credit eligibility checked.";

    case "get_sla_target":
      return "SLA policy checked.";

    case "get_order_details":
      return "Order details checked.";

    case "doc_search":
      return "Relevant documentation checked.";

    case "preview_action":
      return "Action preview prepared.";

    default:
      return "Support check completed.";
  }
}