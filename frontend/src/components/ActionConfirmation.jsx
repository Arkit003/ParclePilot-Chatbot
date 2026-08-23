import { useState } from "react";

import { executeAction } from "../api/actions";


function ActionConfirmation({
  action,
  userId,
  onComplete,
}) {
  const [isSubmitting, setIsSubmitting] =
    useState(false);

  const [error, setError] =
    useState(null);


  const handleAction = async (
    confirmed
  ) => {
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const result =
        await executeAction({
          confirmationId:
            action.confirmationId,
          confirmed,
          userId,
        });

      onComplete?.(result);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to process the action."
      );
    } finally {
      setIsSubmitting(false);
    }
  };


  const amount =
    action.amountInr !== null &&
    action.amountInr !== undefined
      ? `₹${action.amountInr}`
      : null;


  return (
    <div className="action-confirmation">

      <div className="action-confirmation-header">

        <div className="action-confirmation-icon">
          !
        </div>

        <div>
          <div className="action-confirmation-title">
            Confirmation required
          </div>

          <div className="action-confirmation-subtitle">
            This action will change support data.
          </div>
        </div>

      </div>


      <div className="action-confirmation-body">

        <div className="action-field">

          <span className="action-field-label">
            Action
          </span>

          <span className="action-field-value">
            {action.actionType}
          </span>

        </div>


        {action.accountId && (
          <div className="action-field">

            <span className="action-field-label">
              Account
            </span>

            <span className="action-field-value">
              {action.accountId}
            </span>

          </div>
        )}


        {amount && (
          <div className="action-field">

            <span className="action-field-label">
              Amount
            </span>

            <span className="action-field-value">
              {amount}
            </span>

          </div>
        )}


        {action.reason && (
          <div className="action-reason">

            <div className="action-field-label">
              Reason
            </div>

            <div>
              {action.reason}
            </div>

          </div>
        )}

      </div>


      {error && (
        <div className="action-error">
          {error}
        </div>
      )}


      <div className="action-confirmation-actions">

        <button
          type="button"
          className="action-button secondary"
          disabled={isSubmitting}
          onClick={() =>
            handleAction(false)
          }
        >
          Cancel
        </button>


        <button
          type="button"
          className="action-button primary"
          disabled={isSubmitting}
          onClick={() =>
            handleAction(true)
          }
        >
          {isSubmitting
            ? "Processing..."
            : "Confirm action"}
        </button>

      </div>

    </div>
  );
}


export default ActionConfirmation;