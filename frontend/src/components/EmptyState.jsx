function EmptyState() {
  return (
    <div className="empty-state">

      <div className="empty-icon">
        P
      </div>

      <h1>
        How can we help?
      </h1>

      <p>
        Ask about orders, cancellations,
        service credits, SLA targets,
        or ParcelPilot policies.
      </p>

      <div className="suggestions">

        <button>
          Check an order
        </button>

        <button>
          Check an SLA
        </button>

        <button>
          Check cancellation eligibility
        </button>

      </div>

    </div>
  );
}

export default EmptyState;